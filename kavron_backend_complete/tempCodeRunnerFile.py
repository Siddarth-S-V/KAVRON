import uvicorn
from app.core.config import get_settings
if __name__ == "__main__":
    s=get_settings(); uvicorn.run("app.main:app",host=s.host,port=s.port,reload=(s.environment=="development"))
