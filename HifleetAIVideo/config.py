# 火山引擎
huoshan_model_deepseekv3_1 = "deepseek-v3-1-terminus"
huoshan_model_doubaoseed1_6flash = "doubao-seed-1-6-flash-250828"
huoshan_model_doubaoseed1_6vision = "doubao-seed-1-6-vision-250815"
huoshan_base_url = "https://ark.cn-beijing.volces.com/api/v3"
# huoshan_api_key = os.getenv("OPENAI_API_KEY")
huoshan_api_key = "67f8e5b7-61af-4ea1-bf5d-ef9213b2e5df"

# deepseek
deepseek_model_deepseekv3 = "deepseek-chat"
deepseek_model_deepseekr1 = "deepseek-reasoner"
deepseek_base_url = "https://api.deepseek.com"
# deepseek_api_key = os.getenv("OPENAI_API_KEY")
deepseek_api_key = "sk-af635e7fa9b448b7be5fedfc9ba5a740"

#langsmith
langsmith_key = "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"

{   'messages': [HumanMessage(content='事件判断完成：地点=驾驶台, 事件类型=Smoking, 路由=驾驶台_Smoking', additional_kwargs={}, response_metadata={}, id='a1a41cc1-294d-41bf-b4bd-7d0cba366c0d'), 
              AIMessage(content='{\n  "has_human_body": true,\n  "hand_holding_cigarette": true,\n  "smoke_visible": false,\n  "face_visible": true,\n  "smoking_gesture": true,\n  "reason": "图片中检测到人体，手部持有类似香烟的细小棒状物体，人脸清晰可见，人体姿态呈现吸烟相关动作（如手部靠近嘴部或对应姿态），结合事件类型及手部物体判断存在吸烟行为相关特征，烟雾特征暂不明显",\n  "content": "船舶驾驶台内，一名人员处于操作设备、木质椅子及贴满文件的墙面附近，姿态疑似吸烟，手部持有类似香烟的物体，人脸可见，周围有控制台、办公用品等设施"\n}', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 1233, 'prompt_tokens': 636, 'total_tokens': 1869, 'completion_tokens_details': {'accepted_prediction_tokens': None, 'audio_tokens': None, 'reasoning_tokens': 1067, 'rejected_prediction_tokens': None}, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}}, 'model_name': 'doubao-seed-1-6-vision-250815', 'system_fingerprint': None, 'id': '021764227886554a766b838db4ae3400e01419abcbb6b77497bde', 'service_tier': 'default', 'finish_reason': 'stop', 'logprobs': None}, id='run--babb75a3-8239-45ff-b9f9-2e45f72eba65-0', usage_metadata={'input_tokens': 636, 'output_tokens': 1233, 'total_tokens': 1869, 'input_token_details': {'cache_read': 0}, 'output_token_details': {'reasoning': 1067}}), 
              HumanMessage(content='上传完成：事件上传成功：1993845288053395456, matched=1', additional_kwargs={}, response_metadata={}, id='cd4d6138-fce6-4e5a-a1fd-099d7ebecd67')], 
    'video_event_record_id': '1993845288053395456', 
    'camera_name': '驾驶台', 
    'events_type': 'Smoking', 
    'snap_url': 'https://static.hifleet.com/video_event/413587240/803ddca1-bfb7-4b53-b10f-fa674d5c191c.jpeg', 
    'detection_result': {'has_human_body': True, 'hand_holding_cigarette': True, 'smoke_visible': False, 'face_visible': True, 'smoking_gesture': True, 'reason': '图片中检测到人体，手部持有类似香烟的细小棒状物体，人脸清晰可见，人体姿态呈现吸烟相关动作（如手部靠近嘴部或对应姿态），结合事件类型及手部物体判断存在吸烟行为相关特征，烟雾特征暂不明显', 'content': '船舶驾驶台内，一名人员处于操作设备、木质椅子及贴满文件的墙面附近，姿态疑似吸烟，手部持有类似香烟的物体，人脸可见，周围有控制台、办公用品等设施'}, 
    'matched': 1, 
    'reason': '检测到手持香烟且有吸烟动作/烟雾，判定为真实报警', 
    'route_key': '驾驶台_Smoking'
    }
 'video_event_record_id': '1993845288053395456', 
    'camera_name': '驾驶台', 
    'events_type': 'Smoking', 
    'snap_url': 'https://static.hifleet.com/video_event/413587240/803ddca1-bfb7-4b53-b10f-fa674d5c191c.jpeg', 
    'matched': 1, 
    'reason': '检测到手持香烟且有吸烟动作/烟雾，判定为真实报警', 
    'route_key': '驾驶台_Smoking'