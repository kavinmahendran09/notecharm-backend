import os
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
import subprocess
from pathlib import Path

app = FastAPI()

@app.post("/convert/")
async def convert_notebook(file: UploadFile = File(...)):
    # Save the uploaded file temporarily
    temp_file = NamedTemporaryFile(delete=False, suffix=".ipynb")
    with open(temp_file.name, "wb") as f:
        f.write(await file.read())
    
    # Define the output directory (using /tmp for writable directory)
    pdf_output_dir = Path("/tmp/converted_files")  # Change to a writable directory
    pdf_output_dir.mkdir(parents=True, exist_ok=True)

    # Define the output PDF path
    pdf_output_path = pdf_output_dir / f"{Path(temp_file.name).stem}.pdf"

    # Run the conversion command using subprocess
    try:
        # Convert the notebook to PDF using jupyter nbconvert
        subprocess.run(["jupyter", "nbconvert", "--to", "pdf", temp_file.name], check=True)

        # Move the PDF to the output directory
        shutil.move(f"{temp_file.name.replace('.ipynb', '.pdf')}", pdf_output_path)

        # Return the generated PDF file URL
        return JSONResponse(content={"fileUrl": str(pdf_output_path)})
    
    except subprocess.CalledProcessError as e:
        return JSONResponse(content={"error": f"Conversion failed: {e}"}, status_code=500)
    
    finally:
        # Clean up the temporary notebook file
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        if os.path.exists(pdf_output_path):
            os.remove(pdf_output_path)
