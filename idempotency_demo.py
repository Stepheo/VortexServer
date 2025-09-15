"""Демонстрация работы Idempotency-Key."""

import uuid
from typing import Dict, Any
from datetime import datetime, timedelta

# Простой пример хранения результатов операций
class IdempotencyManager:
    def __init__(self):
        # В реальности это Redis или база данных
        self._operations: Dict[str, Dict[str, Any]] = {}
        
    async def get_operation(self, key: str) -> Dict[str, Any] | None:
        """Получить результат операции по ключу."""
        operation = self._operations.get(key)
        if not operation:
            return None
            
        # Проверяем, не истек ли ключ (обычно 24 часа)
        if datetime.now() > operation['expires_at']:
            del self._operations[key]
            return None
            
        return operation
    
    async def store_operation(self, key: str, result: Dict[str, Any]):
        """Сохранить результат операции."""
        self._operations[key] = {
            'result': result,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24)
        }


# Глобальный менеджер (в реальности через DI)
idempotency_manager = IdempotencyManager()


async def upgrade_with_idempotency(
    idempotency_key: str, 
    source_instance_id: str, 
    target_gift_id: int
) -> Dict[str, Any]:
    """Пример апгрейда с идемпотентностью."""
    
    # 1. Проверяем, не выполнялась ли уже эта операция
    existing_result = await idempotency_manager.get_operation(idempotency_key)
    if existing_result:
        print(f"🔄 Возвращаем кешированный результат для {idempotency_key}")
        return existing_result['result']
    
    # 2. Выполняем операцию впервые
    print(f"🆕 Выполняем новую операцию {idempotency_key}")
    
    # Имитация апгрейда
    import random
    success = random.choice([True, False])
    
    result = {
        "txId": str(uuid.uuid4()),
        "success": success,
        "chance": 50.0,
        "finalAngle": random.uniform(0, 360),
        "rotationSpins": random.randint(3, 6),
        "consumedInstanceId": source_instance_id,
        "serverTime": datetime.now().isoformat()
    }
    
    if success:
        result["newItem"] = {
            "instanceId": f"inv_{random.randint(100000, 999999)}",
            "giftId": target_gift_id,
            "name": f"Gift #{target_gift_id}",
            "price": 100.0
        }
    
    # 3. Сохраняем результат
    await idempotency_manager.store_operation(idempotency_key, result)
    
    return result


# Демонстрация
async def demo():
    """Демонстрация работы идемпотентности."""
    
    print("=== Демонстрация Idempotency-Key ===\n")
    
    # Генерируем уникальный ключ
    key = str(uuid.uuid4())
    print(f"🔑 Idempotency-Key: {key}\n")
    
    # Первый запрос
    print("1️⃣ Первый запрос:")
    result1 = await upgrade_with_idempotency(key, "inv_123", 42)
    print(f"Результат: {result1['success']} | TX: {result1['txId'][:8]}...\n")
    
    # Повторный запрос с тем же ключом
    print("2️⃣ Повторный запрос (имитация сетевых проблем):")
    result2 = await upgrade_with_idempotency(key, "inv_123", 42)
    print(f"Результат: {result2['success']} | TX: {result2['txId'][:8]}...\n")
    
    # Проверяем, что результаты идентичны
    if result1 == result2:
        print("✅ Результаты идентичны - идемпотентность работает!")
    else:
        print("❌ Результаты разные - что-то пошло не так!")
    
    print(f"\n🎯 TX ID одинаковый: {result1['txId'] == result2['txId']}")
    print(f"🎯 Success одинаковый: {result1['success'] == result2['success']}")
    
    # Новый ключ = новая операция
    print("\n" + "="*50)
    print("3️⃣ Новый Idempotency-Key = новая операция:")
    new_key = str(uuid.uuid4())
    result3 = await upgrade_with_idempotency(new_key, "inv_456", 84)
    print(f"Новый результат: {result3['success']} | TX: {result3['txId'][:8]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
