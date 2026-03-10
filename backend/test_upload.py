import asyncio
import httpx

async def test_upload():
    # Use python to upload a simple CSV file to the backend
    csv_content = b"prompt,expected_output\nWhat is 2+2?,4\nWhat is the capital of Japan?,Tokyo\n"
    files = {"file": ("test.csv", csv_content, "text/csv")}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post("http://localhost:8000/api/datasets/upload", files=files)
            print("Status:", resp.status_code)
            print("Body:", resp.json())
        except Exception as e:
            print("Error connecting to server:", e)

if __name__ == "__main__":
    asyncio.run(test_upload())
