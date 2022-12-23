# Security Enforced Real Time Tweet Sentiment Analysis

## System Design
<p align="center">
  <img src="https://github.com/SK7here/Security-Enforced-Real-Time-Tweet-Sentiment-Analysis/blob/main/System%20Design.jpeg" width=75% height=75%>
</p>

## Steps for execution:

-	Create kafka topic after starting the zookeeper and kafka servers

    - To start the zookeeper server: <br>
    <b>.\zookeeper-server-start.bat ..\..\config\zookeeper.properties inside kafka\bin\windows</b>

    -	To start the Kafka server <br>
    <b>.\kafka-server-start.bat ..\..\config\server.properties inside kafka\bin\windows</b>

    - To create kafka topic: (inside kafka\bin\windows) <br>
    <b>.\kafka-topics.bat --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic `<kafkatopicname>` </b>

<br>

-	Update the logstash config file with following content to read the tweets through kafka topic and output the tweets into elastic search in their corresponding ports <br>

````
input {
  kafka {
    bootstrap_servers => "localhost:9092"
    topics => "REPLACE YOUR TOPIC NAME"
    }
}

output {
  elasticsearch {
    hosts => ["http://localhost:9200"]
	index => "REPLACE YOUR TOPIC NAME"
  }
}
````


- Start elastic search by running the command <b>"elasticsearch"</b> inside the bin directory of elasticsearch

- Start logstash by running the following command inside logstash folder <br>
  bin\logstash.bat -f config\logstash.conf

- Start Kibana by running the command <b>".\kibana.bat"</b> inside the bin directory of kibana <br>

- To check if elastic search is working fine, type the following command and you should see the attached output<br>
  http://localhost:9200/_cat/indices/kafkatopicname<br>
  
- This should display the health status of the recently created kafka topic as yellow denoting that index is set.
  
- Now the python script <b>'etl_module.py'</b> can be executed


