# RabbitMQ
[完整說明](https://www.rabbitmq.com/)
---
---

Message Queue 簡易說明
----------
------
Message Queue 是一種訊息傳遞仲介，去支持不同process間或不同系統間的非同步訊息傳送，使其能夠做到緩衝。 主要由 Producer, Broker, Consumer 三個部件所組成，且遵循 AMQP 協定
![image](https://miro.medium.com/max/828/1*mIBRudNu5WLDz21-qYsDrQ.webp)


### Message 的優點:
**任務緩衝**

短時間內收到大量請求可能會導致系統過載，特別是 CPU / GPU 運算吃重(heavy computing)的情況，這時候 MQ 就發揮了緩衝的功能，Producer 不需等待地向 Broker 發送訊息(任務)；Consumer 依自己的資源和算力從 Broker 取出適量的訊息(任務)，處理完再繼續拿。

**暫存容錯**

若 Consumer 意外關閉，未處理完的訊息還會存在 MQ 內，並不會丟失，只要再把 Consumer 重啟，又可以接續處理。（通常可設定要暫存或是丟棄）

**系統解耦**

架構設計上拆分為不同元件(components)獨立開發，Producer、Broker 及 Consumer 不需部署在同一台機主機，不需知道彼此的 IP address，也不需使用相同的程式語言。

**水平擴展**

![image](https://enzochang.com/message-queue-introduction/mq_multi.jpg)
Producer 可分散在不同來源、裝置收集（e.g. IoT applications）；Consumer 可以按照需求和資源，運行在多台機器上，加速訊息(任務)的消化和處理


Message Queue 現有工具的比較
----------
------
### 常見工具
![image](https://enzochang.com/message-queue-introduction/mq_product.png)
使用率較高的為 RabbitMQ & Kafka，但使用情境不同

### RabbitMQ vs. Kafka
**RabbitMQ 架構**
![image](https://i.iter01.com/images/db01080701f51e4c648f48c9a03ad45ebc3d038919b3d788c750935b0252551e.png)

**Kafka 架構**
![image](https://i.iter01.com/images/3dda044b35bbf830ef61807734438e0f345819ef20f1a385901fb2a80f0cd3b2.png)


### [RabbitMQ 與 Kafka 其實可看作 Memory-based vs. Log-based](https://homuchen.com/posts/difference-bwtween-rabbitmq-and-kafka/)
#### Memory based
這類系統顧名思義，主要使用memory作為message存放的地方，當consumer ack了某個信息後， 就把它刪掉了，完全不留痕跡。當然很多系統也可以透過設置，決定要不要將信息寫到硬碟上， 不過主要是用來做recovery的，確保broker本身掛掉時，message不會丟失， 當確認了message已經成功抵達了它要到的地方後，一樣會把它刪掉。

此類系統著重的是message從producer到consumer的過程，而不是留下一個永久的狀態或結果。

而信息的傳送是由broker主動```push```給consumer的。

#### Log based
而log based的系統則是相反，只有要message進來，就都寫到硬碟上，是一個append only log， 當consumer要消耗信息時，就是讀取檔案上的資料，讀到盡頭了就等通知， 等有新的資料繼續被append到檔案中，有點像是Unix tool tail -f 的感覺。

此時，信息的傳送consumer去向brokerpull。而為了不讓寫入的速度被限制一個硬碟上，需要將一個topic的log partitioned， 每個partition由一台機器負責，可以獨立地讀寫，像上面的架構圖一樣區分成許多 partition

#### Use Case
(log-based 為 kafka, 另外一個為 rabbitmq)
- 訊息是否需要被保存下來? (Persistence)
    - 如果你想要message被保存下來，那就用log based的messaging system，因為 rabbitmq 主要是儲存在 memory，但近年也開始能透過參數設定其儲存到磁碟，但只能存放到consumer消耗完畢
    - 可以肆無忌憚地去consume message，可以去嘗試、做實驗，不用怕message會不見， 各種event sourcing的好處
- 訊息的工作量大不大? (Load Balancing)
    - log-based 的無法使用大量的consumer來平行地處理所有的工作，因為可以平行工作的consumer的數量受限於partition的數量，在一個partition裡，只要有個message需要耗費很多的時間，就會造成塞車，也就是head of line blocking
    - 而 memory-based 則是自然地support了load balancing，當有message時， broker輪流地向跟他有建立連結的consumer推送信息，就達成了load balancing的效果， 越多consumer，就可以平行處理越多的工作
- 訊息的順序重要嗎? (Inorder Delivery)
    - 有些類型的message彼此是獨立不相干的，被處理順序是如何並不重要，就沒一定要使用log based的產品， 但當你需要保留message的順序時，唯有log based的messaging system可以給你保證，不過只限定於同個partition
- 管理的便捷性
  - rabbitmq 擁有整套的管理套件，不需要與其他的插件做使用；但是 kafka 則需要一些像是 zookeeper 的第三方套件，在管理上比較麻煩

RabbitMQ 部件介紹
----------
------
![image](https://imgconvert.csdnimg.cn/aHR0cHM6Ly9tbWJpei5xcGljLmNuL3N6X21tYml6X3BuZy80aWNWdnd0d1ZleUhpYktNZEZpYUFpYVpweDdvMndKSnRxOTNFNDFxTzI2aWJ6UVN5clJxY2lhNktKNFFyY0NVNFFNcmRGNlJTWHlQQXhPT0MxaWFuMGV0Y2ZRU0EvNjQw?x-oss-process=image/format,png)
### 1. VHost
每一個RabbitMQ服務器可以開設多個虛擬主機vhost（圖中粉色的部分），或者說每一個Broker裡可以開設多個vhost，每一個vhost本質上是一個mini版的RabbitMQ服務器，擁有自己的"交換機exchange、綁定Binding、隊列Queue"，更重要的是每一個vhost擁有獨立的權限機制，這樣就能安全地使用一個RabbitMQ服務器來服務多個應用程序，其中每個vhost服務一個應用程序。

每一個RabbitMQ服務器都有一個默認的虛擬主機"/"，客戶端連接RabbitMQ服務時須指定vHost，如果不指定默認連接的就是"/"
### 2. Connection
無論是生產者還是消費者，都需要和Broker 建立連接，這個連接就是Connection（看圖），是一條TCP 連接，一個生產者或一個消費者與 Broker 之間只有一個Connection，即只有一條TCP連接。

而 Channel 的部分則是因應許多 VHost 而設計的虛擬連接，讓只有一個 TCP 的連線情況下，運作不同與 VHost 的連接。
### 3. Broker
Broker簡單理解就是RabbitMQ服務器，圖中灰色的整個部分。後面說Broker說的就是RabbitMQ服務器。
### 4. Binding
作用就是把exchange和queue按照路由規則綁定起來，一共有四種綁定規則 : Direct, Topic, Fanout, Headers
- Direct：bindings 跟 Message 當中都包含一個「路由鍵（routing keys）」，Broker 可以透過這個 key 將 Message 分配到指定的 Queue。
- Topic：Message 的「路由鍵（routing keys）」與 binding 的「路由鍵（routing keys）」定的模式符合「#」（代替零個或多個層級）或「*」（代替單一層級)，則會將訊息分配到綁定的 queues ，以 Message 「Meow.cat.1」為例，可以符合「Meow.#」或「Meow.cat.*」或「Meow.*.1」的 Queue。
- Fanout：這個模式會從 exchange 分配訊息到綁定的所有 queue，而「路由鍵（routing keys）」會被忽略。
- Headers：透過 Message 的 Header 來判別傳到何者的 queue，其中 x-match 參數為匹配模式，`any` 只要符合就可以匹配，`all` 需要全部都符合才能匹配。



Quickstart
----------
------
### Set up Environment
要開啟 RabbitMQ Server，首先要做以下幾個步驟 (For Windows)，如果要看其他OS的下載方式請點[此連結](https://www.rabbitmq.com/download.html) :

**順著下載即可**
1. [Download](https://www.erlang.org/downloads) Erlang OTP Windows 64-bit installer
2. [Download](https://www.rabbitmq.com/install-windows.html) RabbitMQ Installer
3. 開啟 RabbitMQ Command Prompt，並輸入以下指令確認 rabbitmq 的伺服器有沒有被正確啟動:
```cmd
rabbitmqctl.bat status
```

**要注意在 ```C:\Users\me\.erlang.cookie``` 與 ```C:\Windows\system32\config\systemprofile\.erlang.cookie``` 的值是否相同，不同則會導致無法啟動 RabbitMQ，並持續離線**
**若是不相同，則要uninstall rabbitmq，在把 cookie 們刪掉，然後重新下載。**


### User Interface
1. http://localhost:15672 : 預設帳號與密碼皆為 guest
![image](https://www.cloudamqp.com/img/blog/management-overview.png)

### Build Demo App
1. 先決定要哪種 RabbitMQ 設計模式，舉 Routing (Direct) 為例 :
![image](https://www.rabbitmq.com/img/tutorials/direct-exchange.png)


2.要先創造 producer，舉 emit_log_topic.py 為例:
```
#!/usr/bin/env python
import pika  # pika 是 Rabbitmq 在 Python 裡面操作的套件
import sys

# 創建虛擬 Connection，通常 rabbitmq 的 server 會在 localhost:5672
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# 定義 exchange
channel.exchange_declare(exchange='direct_logs', exchange_type='direct')


severity = sys.argv[1] if len(sys.argv) > 1 else 'info'

# 要傳送的訊息
message = ' '.join(sys.argv[2:]) or 'Hello World!'

# routing_key 指定要傳送到哪一條 queue
channel.basic_publish(
    exchange='direct_logs', routing_key=severity, body=message)
print(" [x] Sent %r:%r" % (severity, message))
connection.close()
```

3. 創建吃訊息的 Consumer，舉 receive_logs_topic.py 為例 : 
```
#!/usr/bin/env python
import pika
import sys

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

severities = sys.argv[1:]
if not severities:
    sys.stderr.write("Usage: %s [info] [warning] [error]\n" % sys.argv[0])
    sys.exit(1)

# 可與 send.py 一樣重複定義 exchange 與 queue 之間的 binding 規則
# Subscribing
for severity in severities:
    channel.queue_bind(
        exchange='direct_logs', queue=queue_name, routing_key=severity)

print(' [*] Waiting for logs. To exit press CTRL+C')


# 接收到訊息後，consumer 要執行的任務
def callback(ch, method, properties, body):
    print(" [x] %r:%r" % (method.routing_key, body))
    # 傳送訊息給 broker(queue) 讓其知道 consumer 已經執行完成
    ch.basic_ack(delivery_tag = method.delivery_tag)

# 定義 consumer 要取哪邊的 queue 取資料
channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()
```

4. 從 consumer 開啟 message queue
```
python receive_logs_direct.py info warning error
# => [*] Waiting for logs. To exit press CTRL+C
```

5. 執行 send.py 以傳送訊息，以檢查 consumer 端有無收到訊息
```
python emit_log_direct.py error "Run. Run. Or it will explode."
# => [x] Sent 'error':'Run. Run. Or it will explode.'
```


### 調整 Binding 策略
除了要先定義在 exchange_type 要使用哪種 binding，還要給相應綁定規則，其主要是在傳給 routing key 的參數上動手 :
1. fanout : 不加東西
2. Topic : 
   1. "#" : 可以替代0個至多個字 (ex : \#.ken\)
   2. "*" : 只能替代一個字 (ex : \*.orange.\*)
3. Header (待更新)


### 相關參數說明
**exchange_declare :** 
1. exchange_type : topic, direct, fanout, header

**basic_publish :**
1. routing_key
2. durable : 設定為 True 時，當 rabbitmq server 突然掛點重啟，會協助保留 queue 裡面的資訊
3. property : 告訴傳送訊息的一些設定
   1. 例如: 我們希望傳送消息能儲存在磁碟，便要更改 delivery mode
   ```
   channel.basic_publish( 
                      properties=pika.BasicProperties( 
                         delivery_mode = pika.spec.PERSISTENT_DELIVERY_MODE 
                      ))
   ```
   2. 因為 rabbitmq 主要是將訊息儲存在 memory 裡，容易有丟失的風險

**queue_declare :**
1. exclusive : 只給一個 connection 做使用，等待該連結完成，即馬上刪除此 queue

**basic_qos :**
1. prefetch_count: 綁定一個 consumer 一次只收一個 work 進來做

**basic_consume**
1. auto_ack : 基本上預設為 True, 也就是 Consumer 處理完任務會回傳一個 ack 給 queue

### 該專案夾層說明
**是以實作專案隔開**

