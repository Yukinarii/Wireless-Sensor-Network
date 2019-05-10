from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('7O73HJIwylbM9bQvBd4Lt1/QvKWxH3RaXFQi2GvfrSWJEP+rYbP9MeNlENq3qDACmttnsvaZVNpEkXnc1L9pRH9K+hee5UEun/ExyJBvYFnFC1gIxciS4Z+QZ42O37USyDOWbZemBkfBeKRqIU4f0wdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('eeac4a6fb266c27b3618e6ae4dccf8c1')

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = TextSendMessage(text=event.message.text)
    line_bot_api.reply_message(event.reply_token, message)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
