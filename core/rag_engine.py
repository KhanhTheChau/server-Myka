import os
import aiohttp
import logging

class RAGEngine:
    def __init__(self):
        self.rag_token = None
        self.rag_robot_id = os.getenv("RAG_ROBOT_ID")
        self.rag_device_secret = os.getenv("RAG_DEVICE_SECRET")
        self.rag_tenant_id = os.getenv("RAG_TENANT_ID")
        self.rag_department_id = os.getenv("RAG_DEPARTMENT_ID", "default")
        
    async def authenticate(self) -> bool:
        if not all([self.rag_robot_id, self.rag_device_secret, self.rag_tenant_id]):
            return False
            
        url = "https://gateway.ihubtech.dev/api/v1/robot/auth"
        payload = {
            "robot_id": self.rag_robot_id,
            "device_secret": self.rag_device_secret
        }
        headers = {"X-Tenant-ID": self.rag_tenant_id}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.rag_token = data.get("jwt")
                        logging.info("RAG Authentication successful.")
                        return True
                    else:
                        logging.error(f"RAG Auth failed: {resp.status} {await resp.text()}")
                        return False
        except Exception as e:
            logging.error(f"RAG Auth error: {e}")
            return False

    async def query(self, question: str, chat_history: list = None) -> dict:
        if not self.rag_token:
            success = await self.authenticate()
            if not success:
                return None
                
        url = f"https://gateway.ihubtech.dev/api/v1/tenants/{self.rag_tenant_id}/departments/{self.rag_department_id}/ask"
        payload = {
            "question": question,
            "chat_history": chat_history or [],
            "session_id": "sess_shared",
            "unit_id": self.rag_robot_id,
            "robot_type": "SENIOR",
            "language": "vi"
        }
        headers = {
            "Authorization": f"Bearer {self.rag_token}",
            "X-Tenant-ID": self.rag_tenant_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status in [401, 403]:
                        self.rag_token = None
                        success = await self.authenticate()
                        if success:
                            headers["Authorization"] = f"Bearer {self.rag_token}"
                            async with session.post(url, json=payload, headers=headers) as retry_resp:
                                if retry_resp.status == 200:
                                    data = await retry_resp.json()
                                    logging.info(f"RAG Query: '{question}' -> Status: {data.get('data', {}).get('status')}")
                                    return data
                        return None
                    elif resp.status == 200:
                        data = await resp.json()
                        logging.info(f"RAG Query: '{question}' -> Status: {data.get('data', {}).get('status')}")
                        return data
                    else:
                        logging.error(f"RAG Query failed: {resp.status} {await resp.text()}")
                        return None
        except Exception as e:
            logging.error(f"RAG Query error: {e}")
            return None
