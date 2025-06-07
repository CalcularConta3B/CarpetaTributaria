from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from playwright.async_api import async_playwright
import os
from fastapi.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CredencialesSII(BaseModel):
    rut: str
    clave: str

@app.post("/analizar")
async def analizar_sii(credenciales: CredencialesSII):
    rut = credenciales.rut
    clave = credenciales.clave

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        try:
            await page.goto("https://zeus.sii.cl/cvc/stc/stc.html")
            await page.fill("#rutcntr", rut.split('-')[0])
            await page.fill("#dvcntr", rut.split('-')[1])
            await page.fill("#clave", clave)
            await page.click("input[type='submit']")
            await page.wait_for_timeout(3000)

            await page.goto("https://www4.sii.cl/cotizacionInternet/validarIngresoEmpresa")
            await page.wait_for_timeout(3000)
            await page.click("input[type='submit']")
            await page.wait_for_timeout(3000)

            download = await page.wait_for_event("download", timeout=10000)
            pdf_path = await download.path()
            save_path = os.path.join("/tmp", f"carpeta_tributaria_{rut}.pdf")
            await download.save_as(save_path)
            await browser.close()

            return FileResponse(save_path, media_type='application/pdf', filename=f"carpeta_tributaria_{rut}.pdf")

        except Exception as e:
            await browser.close()
            return {"error": str(e)}