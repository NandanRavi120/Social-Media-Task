from flask import Flask, request, jsonify # type: ignore
import requests

app = Flask(__name__)

@app.route('/send-data', methods=['POST'])
def send_to_django():
    data = request.json
    django_url = 'http://127.0.0.1:8000/receive/'
    
    try:
        response = requests.post(django_url, json=data)
        response.raise_for_status()
        
        django_response = response.json()
    except requests.RequestException as e:
        print(f'Error sending data to Django: {e}')
        return jsonify({'status': 'failure', 'error': str(e)}), 500
    
    print('Django response:', django_response)
    return jsonify({'status': 'success', 'django_response': django_response}), 200

if __name__ == '__main__':
    app.run(port=5000)
