import requests # type: ignore
import csv
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse

response = requests.get('https://centrojars.com/api/fetchJar/fetchAllTypes.php')
app = FastAPI()


def available():
    # Fetch the types of jars
    response = requests.get('https://centrojars.com/api/fetchJar/fetchAllTypes.php')
    types_data = response.json()

    all_files = []

    # Iterate through types and subtypes to fetch details
    for type_key, subtypes in types_data['response'].items():
        for subtype in subtypes:
            details_url = f'https://centrojars.com/api/fetchJar/{type_key}/{subtype}/fetchAllDetails.php'
            details_response = requests.get(details_url)
            details_data = details_response.json()

            if details_data['status'] == 'success':
                # Extract file information and build a list of dictionaries
                for file_info in details_data['response']['files']:
                    file_entry = {
                        'Type': type_key,
                        'Subtype': subtype,
                        'Version': file_info['version'],
                        'File': file_info['file'],
                        'Size (Display)': file_info['size']['display'],
                        'Size (Bytes)': file_info['size']['bytes'],
                        'MD5': file_info['md5'],
                        'Built': file_info['built'],
                        'Stability': file_info['stability']
                    }
                    all_files.append(file_entry)

    # Return the list of file entries as a JSON response
    return JSONResponse(content={"files": all_files})


@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/available")
async def get_data():
    return available()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="0.0.0.0", port=6969, reload=True)
