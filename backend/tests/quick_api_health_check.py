# -*- coding: utf-8 -*-
"""
Quick API Health Check Script

快速 API 健康检查 - 验证关键 API 是否可访问
"""

import asyncio
import aiohttp


BASE_URL = "http://localhost:8000/api"


async def check_api_health():
    """检查 API 健康状态"""
    print("\n" + "=" * 80)
    print("🏥 API 健康检查")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 健康检查
            print("\n1️⃣  健康检查...")
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 健康检查通过：{data}")
                else:
                    print(f"   ❌ 健康检查失败：{response.status}")
                    return False
            
            # 2. 获取学习阶段（无需认证）
            print("\n2️⃣  获取学习阶段...")
            async with session.get(f"{BASE_URL}/learn/phases") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        phases = data.get("data", [])
                        print(f"   ✅ 获取到 {len(phases)} 个学习阶段")
                    else:
                        print(f"   ⚠️  学习阶段获取失败：{data}")
                else:
                    print(f"   ❌ 学习阶段获取失败：{response.status}")
            
            # 3. 用户注册测试
            print("\n3️⃣  用户注册测试...")
            test_email = f"test_{asyncio.get_event_loop().time()}@example.com"
            payload = {
                "email": test_email,
                "password": "TestPassword123!",
                "username": "测试用户",
            }
            
            async with session.post(f"{BASE_URL}/auth/register", json=payload) as response:
                if response.status == 200:
                    print(f"   ✅ 用户注册成功：{test_email}")
                elif response.status == 400:
                    print(f"   ⚠️  用户已存在：{test_email}")
                else:
                    print(f"   ❌ 用户注册失败：{response.status}")
                    return False
            
            # 4. 用户登录测试
            print("\n4️⃣  用户登录测试...")
            login_payload = {
                "email": test_email,
                "password": "TestPassword123!",
            }
            
            async with session.post(f"{BASE_URL}/auth/login", json=login_payload) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    if token:
                        print(f"   ✅ 用户登录成功，Token: {token[:20]}...")
                        headers = {"Authorization": f"Bearer {token}"}
                        
                        # 5. 获取用户信息
                        print("\n5️⃣  获取用户信息...")
                        async with session.get(f"{BASE_URL}/auth/me", headers=headers) as response:
                            if response.status == 200:
                                user_data = await response.json()
                                print(f"   ✅ 用户信息获取成功")
                            else:
                                print(f"   ❌ 用户信息获取失败：{response.status}")
                        
                        # 6. 进度 Dashboard API 检查
                        print("\n6️⃣  进度 Dashboard API 检查...")
                        async with session.get(
                            f"{BASE_URL}/interview/progress/stats",
                            headers=headers,
                            params={"timeframe": "month"}
                        ) as response:
                            if response.status == 200:
                                stats = await response.json()
                                if stats.get("success"):
                                    print(f"   ✅ 进度统计 API 正常")
                                else:
                                    print(f"   ⚠️  进度统计 API 返回异常：{stats}")
                            else:
                                print(f"   ❌ 进度统计 API 不可用：{response.status}")
                        
                        async with session.get(
                            f"{BASE_URL}/interview/progress/trend",
                            headers=headers,
                            params={"timeframe": "month"}
                        ) as response:
                            if response.status == 200:
                                trend = await response.json()
                                if trend.get("success"):
                                    print(f"   ✅ 分数趋势 API 正常")
                                else:
                                    print(f"   ⚠️  分数趋势 API 返回异常：{trend}")
                            else:
                                print(f"   ❌ 分数趋势 API 不可用：{response.status}")
                        
                        async with session.get(
                            f"{BASE_URL}/interview/progress/heatmap",
                            headers=headers,
                            params={"month": "2026-03"}
                        ) as response:
                            if response.status == 200:
                                heatmap = await response.json()
                                if heatmap.get("success"):
                                    print(f"   ✅ 练习热力图 API 正常")
                                else:
                                    print(f"   ⚠️  练习热力图 API 返回异常：{heatmap}")
                            else:
                                print(f"   ❌ 练习热力图 API 不可用：{response.status}")
                        
                        return True
                    else:
                        print(f"   ❌ 登录响应中缺少 Token")
                        return False
                else:
                    print(f"   ❌ 用户登录失败：{response.status}")
                    return False
                    
        except Exception as e:
            print(f"\n❌ 测试过程中发生异常：{e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🚀 开始 API 健康检查")
    print("=" * 80)
    
    success = await check_api_health()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ API 健康检查通过！系统运行正常")
    else:
        print("❌ API 健康检查失败，请检查后端服务")
    print("=" * 80)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
