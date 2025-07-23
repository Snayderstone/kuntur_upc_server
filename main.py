import uvicorn
from app.server import app

def main():
    uvicorn.run("app.server:app", host="0.0.0.0", port=8050, reload=True)


if __name__ == "__main__":
    main()
