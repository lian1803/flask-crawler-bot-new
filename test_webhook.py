import requests
import json

def test_webhook():
    url = "http://localhost:5000/webhook"
    
    # 카카오톡 챗봇 v2.0 형식으로 테스트
    data = {
        "action": {
            "params": {
                "utterance": "안녕"
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
    test_webhook() 