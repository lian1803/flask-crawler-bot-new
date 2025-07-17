import requests
import json

def test_real_kakao_format():
    url = "http://localhost:5000/webhook"
    
    # 실제 카카오톡 챗봇 빌더에서 오는 형식
    data = {
        "bot": {
            "id": "684fdead98b6403c8db1766e!",
            "name": "와석초 학부모 민원"
        },
        "intent": {
            "id": "684fdeae98b6403c8db17672",
            "name": "폴백 블록",
            "extra": {
                "reason": {
                    "code": 1,
                    "message": "OK"
                }
            }
        },
        "action": {
            "id": "68537685bfa6987bff230167",
            "name": "챗봇",
            "params": {},
            "detailParams": {},
            "clientExtra": {}
        },
        "userRequest": {
            "block": {
                "id": "684fdeae98b6403c8db17672",
                "name": "폴백 블록"
            },
            "user": {
                "id": "d526f20e3f0f1b0ec7030ad081c6c5f8425774e084f7546544d6b0bb0098cd79d3",
                "type": "botUserKey",
                "properties": {
                    "botUserKey": "d526f20e3f0f1b0ec7030ad081c6c5f8425774e084f7546544d6b0bb0098cd79d3",
                    "bot_user_key": "d526f20e3f0f1b0ec7030ad081c6c5f8425774e084f7546544d6b0bb0098cd79d3"
                }
            },
            "utterance": "안녕",
            "params": {
                "ignoreMe": "true",
                "surface": "BuilderBotTest"
            },
            "lang": "ko",
            "timezone": "Asia/Seoul"
        },
        "contexts": [],
        "flow": {
            "lastBlock": {
                "id": "684fdeae98b6403c8db17672",
                "name": "폴백 블록"
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"JSON Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # QuickReplies 확인
            if "template" in result and "outputs" in result["template"]:
                output = result["template"]["outputs"][0]
                if "simpleText" in output and "quickReplies" in output["simpleText"]:
                    print("✅ QuickReplies가 포함되어 있습니다!")
                    print(f"QuickReplies: {output['simpleText']['quickReplies']}")
                else:
                    print("❌ QuickReplies가 없습니다.")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_real_kakao_format() 