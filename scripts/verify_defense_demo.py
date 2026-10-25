"""Navegador, autenticación, cola, juez y tutor de la defensa sin veredictos sembrados."""
import argparse
import json
from pathlib import Path
import re
import time

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="lizardjudge-defensa-20261024")
    parser.add_argument("--require-model", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"lizardjudge-defensa-[a-z0-9][a-z0-9-]{0,40}", args.project):
        parser.error("Solo se admiten proyectos de defensa aislados.")
    state = json.loads((ROOT / ".verification/runtime/defensa" / args.project / "state.json").read_text(encoding="utf-8"))
    root = "http://127.0.0.1:" + str(state["port"])
    output = ROOT / "respaldos/runtime" / args.project
    output.mkdir(parents=True, exist_ok=True)
    rows, feedbacks, errors = [], [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.request.get(root + "/api/profile")
        token = next(item["value"] for item in context.cookies() if item["name"] == "csrftoken")
        response = context.request.post(root+"/api/login", data={"username": "estudiante-demo", "password": state["student_password"]},
                                        headers={"X-CSRFToken": token})
        assert response.ok and not response.json()["error"], "Falló la autenticación de la cuenta ficticia."
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(root+"/problem/DEF-SUMA", wait_until="networkidle")
        start = page.get_by_role("button", name="Iniciar entrenamiento", exact=True)
        if start.is_visible():
            start.click()
        expect(page.get_by_role("button", name="Ayuda del tutor", exact=True)).to_be_visible()

        def submit(code, expected):
            selector = page.locator(".header .ivu-select").first
            selector.click()
            selector.locator(".ivu-select-item").filter(has_text=re.compile(r"^\s*Python3\s*$")).click()
            page.evaluate("code => document.querySelector('.CodeMirror').CodeMirror.setValue(code)", code)
            started = time.monotonic()
            with page.expect_response(lambda r: r.url.endswith("/api/submission") and r.request.method == "POST") as created:
                page.locator("#submit-code").get_by_role("button", name="Enviar").click()
            data = created.value.json()
            assert not data["error"], data
            identifier = data["data"]["submission_id"]
            for _ in range(80):
                data = context.request.get(root+"/api/submission?id="+identifier).json()
                if data["data"]["result"] not in (6,7,9):
                    break
                page.wait_for_timeout(500)
            assert data["data"]["result"] == expected, {"expected": expected, "actual": data["data"]["result"]}
            rows.append({"verdict": expected, "seeded": False, "latency_ms": round((time.monotonic()-started)*1000)})

        def open_panel():
            page.get_by_role("button", name="Recuperar y actualizar", exact=True).click()
            button = page.get_by_role("button", name="Ayuda del tutor", exact=True)
            expect(button).to_be_visible()
            if button.get_attribute("aria-expanded") != "true":
                button.click()

        for level in (1,2,3):
            expression = ("a-b", "a*b", "a+b+1")[level-1]
            submit('a,b=map(int,input().split());print('+expression+')', -1)
            open_panel()
            with page.expect_response(lambda r: r.url.endswith("/api/ai_tutor/feedback") and r.request.method == "POST", timeout=35000) as answered:
                page.get_by_role("button", name="Pista "+str(level), exact=True).click()
            data = answered.value.json()
            assert not data["error"], data
            item = data["data"]
            if args.require_model:
                assert item["source"] == "model", {"level": level, "actual_source": item["source"]}
                assert "Demostración técnica" in item["uncertainty"]
            feedbacks.append({"level": level, "source": item["source"], "model_version": item["model_version"], "latency_ms": item["latency_ms"]})
            expect(page.locator(".tutor-response")).to_be_visible()
            page.screenshot(path=str(output / ("pista-"+str(level)+".png")), full_page=True)
        submit('a,b=map(int,input().split());print(a+b)', 0)
        page.goto(root+"/", wait_until="networkidle")
        expect(page.locator(".personal-practice")).to_contain_text("1 problemas resueltos")
        page.screenshot(path=str(output / "mascota.png"), full_page=True)
        browser.close()
    assert not errors, errors
    (output / "result.json").write_text(json.dumps({"scope": "technical-demo", "real_login": True, "verdicts_seeded": False,
        "production_access": False, "submissions": rows, "feedback": feedbacks, "unique_achievement": 1, "page_errors": errors}, indent=2), encoding="utf-8")
    print("OK: login, tres intentos/pistas, modelo requerido="+str(args.require_model)+", AC y mascota; sin veredictos sembrados.")


if __name__ == "__main__":
    main()
