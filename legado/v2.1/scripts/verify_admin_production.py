"""Regresión de administración exclusivamente sobre una demostración sintética local."""
import argparse
import json
from pathlib import Path
import re
import secrets
import time

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"lizardjudge-defensa-[a-z0-9][a-z0-9-]{0,40}", args.project):
        parser.error("Solo proyectos locales de defensa.")
    state = json.loads((ROOT / ".verification/runtime/defensa" / args.project / "state.json").read_text(encoding="utf-8"))
    root = "http://127.0.0.1:" + str(state["port"])
    output = ROOT / "respaldos/runtime" / args.project / "administracion"
    output.mkdir(parents=True, exist_ok=True)
    errors, routes = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.request.get(root + "/api/profile")
        token = next(item["value"] for item in context.cookies() if item["name"] == "csrftoken")
        headers = {"X-CSRFToken": token}
        def login(target, username, password):
            response = target.request.post(root + "/api/login", data={"username": username, "password": password}, headers=headers)
            assert response.ok and not response.json()["error"], "Falló login ficticio."
        login(context, "docente-demo", state["teacher_password"])
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        def go(route):
            page.goto(root + "/admin/" + route, wait_until="networkidle")
            try:
                expect(page.locator(".admin-sidemenu")).to_be_visible(timeout=15000)
            except AssertionError:
                page.screenshot(path=str(output / "fallo-navegacion.png"), full_page=True)
                raise AssertionError({"route": route, "url": page.url, "errors": errors,
                                      "body": page.locator("body").inner_text()[:400]})
            assert not re.search(r"[\u3400-\u9fff]", page.locator("body").inner_text()), "Texto chino en " + route
            routes.append(route)
        go("problem/edit/1")
        if page.locator(".tags .el-tag").count() == 0:
            page.locator(".button-new-tag").click()
            page.locator(".input-new-tag input").fill("regresion-local")
            page.locator(".input-new-tag input").press("Enter")
        # Incluye submenús inicialmente ocultos: no basta con ver la barra.
        editor = page.locator(".simditor").first
        menus = editor.locator(".simditor-toolbar").evaluate("el => el.textContent + Array.from(el.querySelectorAll('[title]')).map(a=>a.title).join(' ')")
        assert "Insertar fila arriba" in menus and "Alinear a la izquierda" in menus
        assert not re.search(r"[\u3400-\u9fff]", menus)
        expect(editor.locator('[title^="Negrita"]')).to_be_visible()
        original_text = editor.locator(".simditor-body").inner_text()
        page.locator(".el-icon-fa-globe").click()
        page.locator(".el-dropdown-menu__item").filter(has_text=re.compile(r"^English$")).click()
        expect(page.locator(".simditor").first.locator('[title^="Bold"]')).to_be_visible()
        expect(page.locator(".simditor").first.locator(".simditor-body")).to_have_text(original_text)
        page.locator(".el-icon-fa-globe").click()
        page.locator(".el-dropdown-menu__item").filter(has_text="Español (LA)").click()
        expect(page.locator(".simditor").first.locator('[title^="Negrita"]')).to_be_visible()
        page.get_by_role("button", name="Cargar casos guardados", exact=True).click()
        expect(page.locator(".text-case")).to_have_count(3)
        rows = page.locator(".text-case")
        rows.first.locator("textarea").nth(0).fill("10 20\n")
        rows.first.locator("textarea").nth(1).fill("30\n")
        pending = []
        def hold_cases(route):
            if route.request.method == "POST":
                pending.append(route)
            else:
                route.continue_()
        page.route("**/api/admin/test_case/text", hold_cases)
        apply = page.get_by_role("button", name="Aplicar casos de texto", exact=True)
        apply.click()
        page.locator(".el-message-box").get_by_role("button", name="Sí", exact=True).click()
        for _ in range(100):
            if pending:
                break
            page.wait_for_timeout(50)
        assert pending, "No llegó la petición de casos."
        # Cambiar el texto mientras la petición anterior está en vuelo no lo marca aplicado.
        rows.first.locator("textarea").nth(0).fill("100 200\n")
        rows.first.locator("textarea").nth(1).fill("300\n")
        answer = pending[0].fetch()
        pending[0].fulfill(response=answer)
        expect(apply).to_be_enabled()
        page.unroute("**/api/admin/test_case/text", hold_cases)
        page.get_by_role("button", name=re.compile(r"Guardar$")).click()
        expect(page.get_by_text("Aplica los cambios de los casos de texto antes de guardar el problema.", exact=True)).to_be_visible()
        with page.expect_response(lambda r: "/api/admin/test_case/text" in r.url and r.request.method == "POST"):
            apply.click()
            page.locator(".el-message-box").get_by_role("button", name="Sí", exact=True).click()
        expect(apply).to_be_enabled()
        page.screenshot(path=str(output / "casos-texto.png"), full_page=True)
        with page.expect_response(lambda r: "/api/admin/problem" in r.url and r.request.method == "PUT") as saved:
            page.get_by_role("button", name=re.compile(r"Guardar$")).click()
        assert not saved.value.json()["error"], "No se guardó el problema."
        page.wait_for_url(re.compile(r"/admin/problems/?$"))
        fetched = context.request.get(root + "/api/admin/test_case/text?problem_id=1").json()
        assert not fetched["error"] and fetched["data"]["cases"][0] == {"input": "100 200\n", "output": "300\n"}
        go("conf")
        page.get_by_role("button", name="Usar Resend", exact=True).click()
        smtp = page.locator("form").first
        expect(smtp.locator('input[placeholder="smtp.example.com"]')).to_have_value("smtp.resend.com")
        smtp.locator('input[placeholder="email@example.com"]').fill("avisos@example.com")
        synthetic = secrets.token_urlsafe(32)
        smtp.locator('input[type="password"]').fill(synthetic)
        with page.expect_response(lambda r: "/api/admin/smtp" in r.url and r.request.method in ("POST", "PUT")) as saved:
            page.get_by_role("button", name=re.compile(r"Guardar$")).first.click()
        assert not saved.value.json()["error"]
        expect(smtp.locator('input[type="password"]')).to_have_value("")
        with page.expect_response(lambda r: "/api/admin/smtp" in r.url and r.request.method == "PUT") as edited:
            page.get_by_role("button", name=re.compile(r"Guardar$")).first.click()
        assert not edited.value.json()["error"], "Editar sin clave debe conservarla."
        assert "password" not in edited.value.request.post_data_json
        public_config = context.request.get(root + "/api/admin/smtp").json()["data"]
        assert "password" not in public_config and public_config["username"] == "resend"
        assert public_config["ssl"] and not public_config["tls"]
        # No pulsar Enviar prueba: no se autoriza correo externo en una regresión.
        page.screenshot(path=str(output / "smtp-resend.png"), full_page=True)
        for route in ("", "user", "announcement", "judge-server", "problems", "contest"):
            go(route)
        for width in (375, 1280):
            page.set_viewport_size({"width": width, "height": 900})
            for route in ("conf", "problem/edit/1"):
                go(route)
                size = page.evaluate("({width:innerWidth,scroll:document.documentElement.scrollWidth})")
                assert size["scroll"] <= size["width"], {"route": route, **size}
                if width == 375 and route == "conf":
                    field = page.locator('input[placeholder="smtp.example.com"]')
                    assert field.bounding_box()["width"] > 200, "Campo SMTP demasiado estrecho en móvil."
                page.screenshot(path=str(output / (route.split('/')[0] + '-' + str(width) + '.png')), full_page=True)
        student = browser.new_context()
        student.request.get(root + "/api/profile")
        student_token = next(item["value"] for item in student.cookies() if item["name"] == "csrftoken")
        student_headers = {"X-CSRFToken": student_token}
        response = student.request.post(root + "/api/login", data={"username": "estudiante-demo", "password": state["student_password"]}, headers=student_headers)
        assert not response.json()["error"]
        # Django rota el token CSRF al autenticar la sesión.
        student_headers = {"X-CSRFToken": next(item["value"] for item in student.cookies() if item["name"] == "csrftoken")}
        assert student.request.get(root + "/api/admin/test_case/text?problem_id=1").json()["error"]
        verdicts = []
        for code, verdict in (("print(5)", -1), ("a,b=map(int,input().split());print(a+b)", 0)):
            created = student.request.post(root + "/api/submission", data={"problem_id": 1, "language": "Python3", "code": code}, headers=student_headers).json()
            assert not created["error"], "Falló creación del envío."
            identifier = created["data"]["submission_id"]
            for _ in range(100):
                result = student.request.get(root + "/api/submission?id=" + identifier).json()["data"]["result"]
                if result not in (6, 7, 9):
                    break
                time.sleep(0.3)
            assert result == verdict, {"expected": verdict, "actual": result}
            verdicts.append(result)
        browser.close()
    assert not errors, errors
    (output / "result.json").write_text(json.dumps({"production_access": False, "routes": routes,
        "page_errors": errors, "text_cases_saved_and_judged": True, "verdicts": verdicts,
        "smtp_external_email_sent": False, "smtp_resend_saved": True,
        "blank_password_omitted": True, "mobile_widths": [375, 1280]}, indent=2), encoding="utf-8")
    print("OK: administración, menús traducidos, casos en texto juzgados, SMTP Resend sin correo externo y móvil.")


if __name__ == "__main__":
    main()
