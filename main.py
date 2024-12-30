import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
from pathlib import Path
import subprocess

app = FastAPI()

@app.post("/convert/")
async def convert_notebook(file: UploadFile = File(...)):
    # Save the uploaded file temporarily
    temp_file = NamedTemporaryFile(delete=False, suffix=".ipynb")
    try:
        with open(temp_file.name, "wb") as f:
            f.write(await file.read())

        # Define the output directory (using /tmp for writable directory in cloud)
        pdf_output_dir = Path("/tmp/converted_files")  # Cloud writable directory
        pdf_output_dir.mkdir(parents=True, exist_ok=True)

        # Define the output PDF path
        pdf_output_path = pdf_output_dir / f"{Path(temp_file.name).stem}.pdf"

        # Run the conversion command using subprocess
        conversion_command = [
            "jupyter",
            "nbconvert",
            "--to",
            "pdf",
            temp_file.name
        ]
        result = subprocess.run(
            conversion_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Conversion failed: {result.stderr.decode('utf-8')}"
            )

        # Move the generated PDF to the output directory
        output_pdf_name = temp_file.name.replace(".ipynb", ".pdf")
        shutil.move(output_pdf_name, pdf_output_path)

        # Construct a public URL for the file
        file_url = f"https://notecharm-backend-production.up.railway.app/files/{pdf_output_path.name}"

        return JSONResponse(content={"fileUrl": file_url})

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )

    finally:
        # Clean up the temporary notebook file
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


@app.get("/files/{filename}")
async def serve_file(filename: str):
    """
    Serve the converted files for download.
    """
    file_path = Path(f"/tmp/converted_files/{filename}")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return JSONResponse(content={"fileUrl": str(file_path)})
