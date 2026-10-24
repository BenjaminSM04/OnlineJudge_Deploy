"""Ensayo HTTP y Chromium real; los veredictos se siembran y no prueban el juez."""
import argparse
import json
from pathlib import Path
import subprocess
import uuid

from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    if not args.project.startswith("lizardjudge-upgrade-"):
        parser.error("Solo se permiten proyectos de actualización aislados.")
    compose = ["docker", "compose", "-p", args.project, "-f", "compose.upgrade-verify.yml"]

    def backend(code):
        prefix = 'import os; assert os.environ.get("OJ_VERIFICATION_ONLY") == "1"\n'
        result = subprocess.check_output(compose + ["exec", "-T", "oj-backend", "python", "manage.py", "shell", "--verbosity", "0"], input=prefix + code, encoding="utf-8")
        return json.loads(result.strip().splitlines()[-1])

    identifier = "UI-" + uuid.uuid4().hex[:10]
    fixture = backend('''
import json, secrets
from account.models import User, UserProfile, AdminType, ProblemPermission
from problem.tests import DEFAULT_PROBLEM_DATA, ProblemCreateTestBase
from ai_tutor.models import TutorProblemConfig, TutorProblemConfigVersion
from ai_tutor.tests.config_factory import config_content
from ai_tutor.services.problem_config import create_draft, activate_version
from django.contrib.sessions.backends.cache import SessionStore
user = User(username="''' + identifier + '''", admin_type=AdminType.SUPER_ADMIN, problem_permission=ProblemPermission.ALL)
user.set_password(secrets.token_urlsafe(32)); user.save()
UserProfile.objects.create(user=user, language="es-LA")
problem = ProblemCreateTestBase.add_problem(dict(DEFAULT_PROBLEM_DATA, _id="''' + identifier + '''"), user)
content = config_content()
content.update(concepts=["Acumulador"], concept_explanations={"Acumulador": "Un acumulador conserva un resultado parcial mientras recorres los valores."})
version = create_draft(user, problem.id, **content)
activate_version(user, problem.id, version.id)
TutorProblemConfig.objects.update_or_create(problem=problem, defaults={"enabled": True, "updated_by": user})
store = SessionStore(); store["_auth_user_id"] = str(user.id); store["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"; store["_auth_user_hash"] = user.get_session_auth_hash(); store.save()
user.session_keys = [store.session_key]; user.save()
print(json.dumps({"user": user.id, "problem": problem.id, "cookie": store.session_key}))
''')
    root = "http://127.0.0.1:18082"
    output = Path("respaldos/runtime/ui") / identifier
    output.mkdir(parents=True)
    results = []
    errors = []

    def attempt(accepted=False, display=None):
        return backend('''
import json
from account.models import User
from submission.models import Submission
from problem.models import Problem
from problem.tests import DEFAULT_PROBLEM_DATA, ProblemCreateTestBase
user = User.objects.get(pk=''' + str(fixture["user"]) + ''')
problem = Problem.objects.get(pk=''' + str(fixture["problem"]) + ''')
''' + (f'problem = ProblemCreateTestBase.add_problem(dict(DEFAULT_PROBLEM_DATA, _id="{display}"), user)\n' if display else "") + '''
submission = Submission.objects.create(user_id=user.id, username=user.username, problem=problem, language="Python3", code="print(0)", result=''' + ("0" if accepted else "-1") + ''')
print(json.dumps({"submission": submission.id}))
''')

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 375, "height": 850}, reduced_motion="reduce")
        context.add_cookies([{"name": "sessionid", "value": fixture["cookie"], "url": root, "httpOnly": True, "sameSite": "Lax"}])
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))

        def api(path, body=None, method=None):
            return page.evaluate('''async ({path, body, method}) => {
              const token = document.cookie.split('; ').find(x => x.startsWith('csrftoken='));
              const response = await fetch(path, {method: method || (body ? 'POST' : 'GET'), headers: {'Content-Type': 'application/json', 'X-CSRFToken': token ? token.split('=')[1] : ''}, body: body ? JSON.stringify(body) : undefined});
              return {status: response.status, ...await response.json()};
            }''', {"path": path, "body": body, "method": method})

        page.goto(root + "/problem/" + identifier, wait_until="networkidle")
        expect(page.get_by_role("button", name="Iniciar entrenamiento", exact=True)).to_be_visible()
        page.get_by_role("button", name="Iniciar entrenamiento", exact=True).click()
        expect(page.get_by_role("button", name="Ayuda del tutor", exact=True)).to_be_visible()
        attempt()

        def refresh():
            page.get_by_role("button", name="Recuperar y actualizar", exact=True).click()
            expect(page.get_by_role("button", name="Ayuda del tutor", exact=True)).to_be_visible()
            page.get_by_role("button", name="Ayuda del tutor", exact=True).click()
            expect(page.get_by_role("button", name="Explicar mi último intento", exact=True)).to_be_enabled()

        refresh()
        page.get_by_role("button", name="Explicar mi último intento", exact=True).click()
        expect(page.locator(".tutor-response")).to_contain_text("Ayuda de respaldo")
        expect(page.get_by_role("button", name="Pista 2", exact=True)).to_be_disabled()
        page.get_by_role("button", name="Pista 1", exact=True).click()
        expect(page.locator(".training-session > p[role=status]")).to_contain_text("1")
        expect(page.get_by_role("button", name="Pista 2", exact=True)).to_be_disabled()
        for level in (2, 3):
            attempt()
            refresh()
            button = page.get_by_role("button", name=f"Pista {level}", exact=True)
            expect(button).to_be_enabled()
            button.click()
            expect(page.locator(".training-session > p[role=status]")).to_contain_text(f"ayuda: {level}")
        page.locator(".tutor-panel select").select_option("Acumulador")
        page.get_by_role("button", name="Explicar concepto", exact=True).click()
        expect(page.locator(".tutor-response")).to_contain_text("Un acumulador conserva")
        useful = page.get_by_role("button", name="Me resultó útil", exact=True)
        useful.click()
        expect(useful).to_have_attribute("aria-pressed", "true")
        session = api("/api/ai_tutor/session?problem_id=" + str(fixture["problem"]))["data"]
        assert session["highest_help_level"] == 3 and len(session["feedback"]) == 5
        initial_version = session["config_version_id"]
        results.append({"flow": "explain-hints123-concept-rating", "feedback": 5, "synthetic_verdicts": True})
        page.screenshot(path=str(output / "tutor.png"), full_page=True)
        page.reload(wait_until="networkidle")
        page.get_by_role("button", name="Ayuda del tutor", exact=True).click()
        page.get_by_role("button", name="Pista 1", exact=True).click()
        expect(page.locator(".tutor-response")).to_be_visible()
        assert len(api("/api/ai_tutor/session?problem_id=" + str(fixture["problem"]))["data"]["feedback"]) == 5

        # Logros: resultados de fixtures explícitos, nunca una certificación del juez.
        for index in range(5):
            attempt(accepted=True, display=identifier + "-AC-" + str(index))
        page.goto(root + "/", wait_until="networkidle")
        practice = page.locator(".personal-practice")
        expect(practice).to_contain_text("5 problemas resueltos")
        practice.get_by_text("Personalizar mi mascota", exact=True).click()
        practice.locator("select").nth(0).select_option("blue")
        expect(practice.locator("select").nth(0)).to_be_enabled()
        practice.locator("select").nth(1).select_option("scarf")
        expect(practice.locator("select").nth(1)).to_be_enabled()
        expect(practice.locator(".mascot")).to_have_css("animation-name", "none")
        page.reload(wait_until="networkidle")
        assert api("/api/mascot")["data"]["appearance"] == {"color": "blue", "accessory": "scarf"}
        results.append({"flow": "mascot-unlocks-persistence-reduced-motion", "passed": True})

        # Tema y navegación por teclado sobre una preferencia guardada.
        page.get_by_role("button", name="Modo oscuro", exact=True).focus()
        page.keyboard.press("Enter")
        expect(page.locator("html")).to_have_attribute("data-lizard-theme", "dark")
        page.reload(wait_until="networkidle")
        expect(page.locator("html")).to_have_attribute("data-lizard-theme", "dark")
        for width in (320, 375, 1280):
            page.set_viewport_size({"width": width, "height": 850})
            for route in ("/", "/problem/" + identifier, "/setting/profile"):
                page.goto(root + route, wait_until="networkidle")
                dimensions = page.evaluate("({width:innerWidth, scroll:document.documentElement.scrollWidth})")
                assert dimensions["scroll"] <= width + 1, (route, dimensions)
                page.screenshot(path=str(output / (str(width) + route.replace("/", "_") + ".png")), full_page=True)
                results.append({"route": route, **dimensions, "theme": "dark"})

        page.goto(root + "/admin/problem/edit/" + str(fixture["problem"]), wait_until="networkidle")
        pedagogy = page.locator(".pedagogy")
        expect(pedagogy).to_be_visible()
        pedagogy.locator("select").select_option("")
        pedagogy.locator("input").first.fill("Iteracion")
        for textarea, value in zip(pedagogy.locator("textarea").all(), ["Recorre cada valor conservando el estado parcial.", "Identifica el concepto que conecta los datos.", "Revisa donde cambia el estado parcial.", "Traza los pasos con valores pequenos."]):
            textarea.fill(value)
        pedagogy.get_by_role("button", name="Guardar nuevo borrador", exact=True).click()
        expect(pedagogy.get_by_role("status")).to_contain_text("Borrador guardado")
        pedagogy.get_by_role("button", name="Activar borrador seleccionado", exact=True).click()
        expect(pedagogy.get_by_role("status")).to_contain_text("Versión activada")
        current = api("/api/ai_tutor/session?problem_id=" + str(fixture["problem"]))["data"]
        assert current["config_version_id"] == initial_version
        results.append({"flow": "teacher-draft-activation-existing-session-pinned", "passed": True})
        page.screenshot(path=str(output / "teacher.png"), full_page=True)
        editors = page.locator(".simditor-body")
        expect(editors.first).to_be_visible()
        editors.first.fill("Contenido de ensayo con formula $a+b$ y texto.")
        upload = page.locator(".toolbar-item-uploadfile input[type=file]").first
        with page.expect_response(lambda response: "/api/admin/upload_file" in response.url) as uploaded:
            upload.set_input_files({"name": "ensayo.pdf", "mimeType": "application/pdf", "buffer": b"%PDF-1.4\n% synthetic upload fixture\n%%EOF\n"})
        response = uploaded.value
        assert response.status == 200 and response.json()["success"]
        assert response.request.header_value("x-csrftoken")
        expect(editors.first.locator("a", has_text="ensayo.pdf")).to_be_visible()
        download = context.request.get(root + response.json()["file_path"])
        assert "attachment" in download.headers.get("content-disposition", "")
        assert download.headers.get("x-content-type-options") == "nosniff"
        results.append({"flow": "simditor-editor-upload-csrf-download-headers", "passed": True})

        denied = page.evaluate('''async () => {
          const r = await fetch('/api/mascot', {method:'PATCH',headers:{'Content-Type':'application/json'},body:'{"visible":false}'});
          return r.status;
        }''')
        assert denied == 403
        page.goto(root + "/admin/user", wait_until="networkidle")
        page.locator("input[type=file]").first.set_input_files({"name": "ensayo.csv", "mimeType": "text/csv", "buffer": (identifier + "," + uuid.uuid4().hex + ",example@example.invalid,Ensayo\n").encode()})
        expect(page.get_by_role("button", name="Importar Usuarios")).to_be_visible()
        expect(page.locator(".el-table").filter(has_text="example@example.invalid")).to_be_visible()
        results.append({"flow": "csv-preview-without-import-and-csrf-denied", "passed": True})
        assert not errors, errors
        browser.close()
    report = {"project": args.project, "browser": "Chromium", "production_access": False, "judge_execution": False, "model_inference": False, "page_errors": errors, "results": results}
    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("OK: interfaz y API reales; " + str(len(results)) + " comprobaciones. Evidencia: " + str(output / "results.json"))


if __name__ == "__main__":
    main()
