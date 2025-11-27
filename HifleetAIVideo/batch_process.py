"""
批量处理船舶报警事件
从imgUrl.txt文件中读取数据，批量调用Agent进行分析
"""
import csv
import json
from pathlib import Path
from config import langsmith_key
from shipAlertAgent import create_ship_alert_workflow


def read_img_url_file(file_path: str):
    """读取imgUrl.txt文件"""
    results = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            results.append({
                'video_event_record_id': row['video_event_record_id'],
                'camera_name': row['camera_name'],
                'events_type': row['events_type'],
                'snap_url': row['snap_url'],
                'matched_expected': int(row['matched'])  # 期望的结果（用于对比）
            })
    return results


def process_single_event(app, event_data, thread_id: str = "batch_session"):
    """处理单个事件"""
    thread_config = {"configurable": {"thread_id": f"{thread_id}_{event_data['video_event_record_id']}"}}
    
    input_data = {
        "messages": [],
        "video_event_record_id": event_data['video_event_record_id'],
        "camera_name": event_data['camera_name'],
        "events_type": event_data['events_type'],
        "snap_url": event_data['snap_url'],
        "detection_result": {},
        "matched": 0,
        "reason": "",
        "route_key": ""
    }
    
    try:
        result = app.invoke(input_data, config=thread_config)
        return {
            "success": True,
            "result": result,
            "matched_predicted": result.get('matched', 0),
            "matched_expected": event_data['matched_expected'],
            "is_correct": result.get('matched', 0) == event_data['matched_expected']
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "matched_predicted": None,
            "matched_expected": event_data['matched_expected'],
            "is_correct": False
        }


def batch_process(file_path: str = "dataset/imgUrl.txt", limit: int = None):
    """批量处理事件"""
    print("=" * 60)
    print("开始批量处理船舶报警事件")
    print("=" * 60)
    
    # 读取数据
    events = read_img_url_file(file_path)
    if limit:
        events = events[:limit]
    
    print(f"共读取 {len(events)} 个事件\n")
    
    # 创建工作流
    app = create_ship_alert_workflow()
    
    # 处理结果
    results = []
    correct_count = 0
    total_count = 0
    
    # mysql
    import pymysql
    from pymysql import Error
    db_config = {
    'host': 'localhost',    # 本地数据库，固定为localhost
    'user': 'root',         # 数据库用户名（默认root）
    'password': 'lurui...',  # 替换为你重置后的密码
    'database': 'HifleetAIVideo_db', # 目标数据库名
    'port': 3306,           # MySQL默认端口（无需修改）
    'charset': 'utf8mb4'    # 支持中文（避免乱码）
    }   
    ##########################
    try:
    ## 连接MySQL数据库
        connection = pymysql.connect(**db_config)
        if connection.open:
            print("✅ 数据库连接成功！")

        # 4. 创建游标（用于执行SQL语句）
        cursor = connection.cursor()
        insert_sql = """
            INSERT INTO ship_smoking_events (
                video_event_record_id, 
                camera_name, 
                events_type, 
                snap_url, 
                matched, 
                reason, 
                route_key
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        for i, event in enumerate(events, 1):
            print(f"[{i}/{len(events)}] 处理事件: {event['video_event_record_id']} - {event['camera_name']} - {event['events_type']}")
            
            process_result = process_single_event(app, event)
            results.append({
                "event": event,
                "process_result": process_result
            })
            #### 插入到 mysql数据库
            llm_state = process_result['result']
            insert_data = (
                int(llm_state['video_event_record_id']),  # 转整数（匹配表中BIGINT类型）
                llm_state['camera_name'],
                llm_state['events_type'],
                llm_state['snap_url'],
                llm_state['matched'],
                llm_state['reason'],
                llm_state['route_key']
            )
            #执行SQL语句
            cursor.execute(insert_sql, insert_data)
            # 提交事务（MySQL默认手动提交，必须执行此步才会写入数据库）
            connection.commit()
            print(f"✅ 数据插入成功！插入行数：{cursor.rowcount}")
            ####
            
            if process_result['success']:
                total_count += 1
                if process_result['is_correct']:
                    correct_count += 1
                    status = "✓ 正确"
                else:
                    status = "✗ 错误"
                
                print(f"  预测结果: {process_result['matched_predicted']}, 期望结果: {process_result['matched_expected']}, {status}")
                print(f"  判断原因: {process_result['result'].get('reason', 'N/A')[:100]}")
            else:
                print(f"  ✗ 处理失败: {process_result['error']}")
            
            print()
        
        ###
    except Error as e:
        # 若出错，回滚事务（避免数据混乱）
        connection.rollback()
        print(f"❌ 操作失败：{e}")

    finally:
        # 8. 关闭游标和连接（释放资源）
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()
            print("🔌 数据库连接已关闭")    
    ##########################
    # 统计结果
    print("=" * 60)
    print("批量处理完成")
    print("=" * 60)
    print(f"总事件数: {len(events)}")
    print(f"成功处理: {total_count}")
    print(f"处理失败: {len(events) - total_count}")
    if total_count > 0:
        print(f"准确率: {correct_count}/{total_count} = {correct_count/total_count*100:.2f}%")
    print()
    
    # 保存详细结果
    output_file = "batch_process_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"详细结果已保存到: {output_file}")
    
    # 保存摘要报告
    summary = {
        "total_events": len(events),
        "success_count": total_count,
        "failed_count": len(events) - total_count,
        "correct_count": correct_count,
        "accuracy": correct_count / total_count if total_count > 0 else 0,
        "details": [
            {
                "video_event_record_id": r["event"]["video_event_record_id"],
                "camera_name": r["event"]["camera_name"],
                "events_type": r["event"]["events_type"],
                "matched_predicted": r["process_result"].get("matched_predicted"),
                "matched_expected": r["event"]["matched_expected"],
                "is_correct": r["process_result"].get("is_correct", False),
                "success": r["process_result"].get("success", False)
            }
            for r in results
        ]
    }
    
    summary_file = "batch_process_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"摘要报告已保存到: {summary_file}")
    
    return results, summary


if __name__ == "__main__":
    # 批量处理（可以设置limit参数限制处理数量，用于测试）
    ### 配置langsmith
    import os
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = langsmith_key
    os.environ["LANGCHAIN_PROJECT"] = "HifleetAIVideo"

    batch_process("AIProject/HifleetAIVideo/dataset/imgUrl.txt", limit=None)  # limit=None表示处理所有事件

