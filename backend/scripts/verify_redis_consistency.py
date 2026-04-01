"""
Redis Data Consistency Verification Script

验证 Dual-write 策略下 Redis 和内存数据的一致性。
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.redis_client import get_redis_client
from app.agents.interview_agent import InterviewState


async def verify_redis_connection():
    """验证 Redis 连接是否正常"""
    print("=" * 60)
    print("Redis 连接验证")
    print("=" * 60)
    
    try:
        redis_client = get_redis_client()
        
        # 测试连接
        await redis_client.redis.ping()
        print("✅ Redis 连接成功")
        
        # 获取所有面试会话 key
        keys = await redis_client.redis.keys("interview:*")
        print(f"📊 当前 Redis 中有 {len(keys)} 个面试会话")
        
        if keys:
            print("\n会话列表:")
            for key in keys[:10]:  # 显示前 10 个
                ttl = await redis_client.redis.ttl(key)
                print(f"  - {key} (TTL: {ttl}s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis 连接失败：{e}")
        return False


async def verify_dual_write_consistency():
    """验证 Dual-write 数据一致性"""
    print("\n" + "=" * 60)
    print("Dual-write 数据一致性验证")
    print("=" * 60)
    
    try:
        from app.api.interview import active_sessions
        
        redis_client = get_redis_client()
        
        # 获取内存中的会话
        memory_count = len(active_sessions)
        print(f"📊 内存中的活跃会话数：{memory_count}")
        
        if memory_count == 0:
            print("💡 内存中没有活跃会话（这是正常的）")
            return True
        
        # 对比 Redis 中的数据
        redis_keys = await redis_client.redis.keys("interview:*")
        redis_count = len(redis_keys)
        print(f"📊 Redis 中的会话数：{redis_count}")
        
        # 检查每个内存会话是否在 Redis 中存在
        print("\n逐一比对会话:")
        consistent_count = 0
        missing_in_redis = []
        
        for session_id in active_sessions.keys():
            redis_key = f"interview:{session_id}"
            exists_in_redis = await redis_client.redis.exists(redis_key)
            
            if exists_in_redis:
                print(f"  ✅ {session_id} - Redis 中存在")
                consistent_count += 1
            else:
                print(f"  ❌ {session_id} - Redis 中缺失")
                missing_in_redis.append(session_id)
        
        # 计算一致性比率
        if memory_count > 0:
            consistency_rate = (consistent_count / memory_count) * 100
            print(f"\n📈 数据一致性：{consistency_rate:.1f}% ({consistent_count}/{memory_count})")
        
        if missing_in_redis:
            print(f"\n⚠️  警告：{len(missing_in_redis)} 个会话在 Redis 中缺失")
            print("   可能的原因:")
            print("   1. Redis 写入时发生异常")
            print("   2. Redis TTL 已过期")
            print("   3. Redis 服务曾重启")
            return False
        else:
            print("\n✅ Dual-write 数据一致性良好")
            return True
            
    except Exception as e:
        print(f"❌ 验证失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_redis_read_write():
    """测试 Redis 读写功能"""
    print("\n" + "=" * 60)
    print("Redis 读写功能测试")
    print("=" * 60)
    
    try:
        redis_client = get_redis_client()
        test_session_id = "test-session-" + str(asyncio.get_event_loop().time())
        
        # 创建测试数据
        test_state = InterviewState(
            session_id=test_session_id,
            job_role="测试工程师",
            tech_stack=["Python", "FastAPI"],
            difficulty_level="easy",
            current_question="这是一个测试问题",
            question_number=1,
            total_questions=5,
            conversation_history=[],
            is_finished=False,
        )
        
        # 测试写入
        print(f"📝 写入测试会话：{test_session_id}")
        write_result = await redis_client.save_session(test_session_id, test_state, ttl=60)
        print(f"   写入结果：{'✅ 成功' if write_result else '❌ 失败'}")
        
        # 测试读取
        print("📖 读取测试会话...")
        read_state = await redis_client.get_session(test_session_id)
        
        if read_state:
            print(f"   读取结果：✅ 成功")
            print(f"   会话 ID: {read_state.session_id}")
            print(f"   岗位：{read_state.job_role}")
            print(f"   问题数：{read_state.question_number}/{read_state.total_questions}")
            
            # 清理测试数据
            print("🧹 清理测试数据...")
            await redis_client.delete_session(test_session_id)
            print("   清理完成")
            
            return True
        else:
            print(f"   读取结果：❌ 失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🔍 Redis 数据一致性验证工具")
    print("=" * 60)
    
    # 1. 验证 Redis 连接
    redis_ok = await verify_redis_connection()
    
    if not redis_ok:
        print("\n❌ Redis 连接失败，请检查 Redis 服务是否启动")
        return
    
    # 2. 测试 Redis 读写
    rw_ok = await test_redis_read_write()
    
    # 3. 验证 Dual-write 一致性
    consistent = await verify_dual_write_consistency()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 验证总结")
    print("=" * 60)
    print(f"Redis 连接：{'✅ 正常' if redis_ok else '❌ 异常'}")
    print(f"读写测试：{'✅ 正常' if rw_ok else '❌ 异常'}")
    print(f"数据一致性：{'✅ 良好' if consistent else '⚠️  存在问题'}")
    
    if redis_ok and rw_ok and consistent:
        print("\n✅ Redis Dual-write 系统运行正常")
    else:
        print("\n⚠️  发现问题，需要进一步检查")


if __name__ == "__main__":
    asyncio.run(main())
