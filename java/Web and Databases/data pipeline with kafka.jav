// === pom.xml dependencies ===
// kafka-clients, slf4j-simple

import org.apache.kafka.clients.producer.*;
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.serialization.*;
import java.util.*;
import java.time.*;
import java.util.concurrent.*;

class DataPipeline {
    private final String bootstrapServers = "localhost:9092";
    
    public Producer<String, String> createProducer(String clientId) {
        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ProducerConfig.CLIENT_ID_CONFIG, clientId);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.RETRIES_CONFIG, 3);
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        
        return new KafkaProducer<>(props);
    }

    public Consumer<String, String> createConsumer(String groupId, String clientId) {
        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);
        props.put(ConsumerConfig.CLIENT_ID_CONFIG, clientId);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);
        
        return new KafkaConsumer<>(props);
    }

    public void produceMessages(String topic, int count) throws InterruptedException {
        try (Producer<String, String> producer = createProducer("producer-1")) {
            for (int i = 0; i < count; i++) {
                String key = "key-" + (i % 5);
                String value = String.format("{\"id\":%d,\"timestamp\":%d,\"data\":\"Message %d\"}",
                    i, System.currentTimeMillis(), i);
                
                ProducerRecord<String, String> record = new ProducerRecord<>(topic, key, value);
                
                producer.send(record, (metadata, exception) -> {
                    if (exception == null) {
                        System.out.printf("Sent: key=%s, partition=%d, offset=%d%n",
                            key, metadata.partition(), metadata.offset());
                    } else {
                        System.err.println("Error sending message: " + exception.getMessage());
                    }
                });
                
                Thread.sleep(100);
            }
            producer.flush();
            System.out.println("Produced " + count + " messages to topic: " + topic);
        }
    }

    public void consumeMessages(String topic, String groupId, int maxMessages) {
        try (Consumer<String, String> consumer = createConsumer(groupId, "consumer-" + groupId)) {
            consumer.subscribe(Arrays.asList(topic));
            
            int count = 0;
            while (count < maxMessages) {
                ConsumerRecords<String, String> records = consumer.poll(1000);
                
                for (ConsumerRecord<String, String> record : records) {
                    System.out.printf("Consumed: topic=%s, partition=%d, offset=%d, key=%s, value=%s%n",
                        record.topic(), record.partition(), record.offset(),
                        record.key(), record.value());
                    count++;
                }
                
                consumer.commitSync();
            }
            System.out.println("Consumed " + count + " messages from topic: " + topic);
        }
    }

    public void processStream(String sourceTopic, String destTopic) {
        try (Consumer<String, String> consumer = createConsumer("stream-processor", "stream-processor");
             Producer<String, String> producer = createProducer("stream-processor-producer")) {
            
            consumer.subscribe(Arrays.asList(sourceTopic));
            
            while (true) {
                ConsumerRecords<String, String> records = consumer.poll(1000);
                
                for (ConsumerRecord<String, String> record : records) {
                    // Transform data
                    String transformed = transformData(record.value());
                    
                    ProducerRecord<String, String> newRecord = new ProducerRecord<>(
                        destTopic, record.key(), transformed
                    );
                    
                    producer.send(newRecord);
                    System.out.println("Processed: " + record.key() + " -> " + destTopic);
                }
                
                consumer.commitSync();
                producer.flush();
            }
        }
    }

    private String transformData(String data) {
        // Simple transformation - add processing timestamp
        return data.substring(0, data.length() - 1) + 
            ",\"processed_at\":" + System.currentTimeMillis() + "}";
    }

    public static void main(String[] args) throws InterruptedException {
        DataPipeline pipeline = new DataPipeline();
        String sourceTopic = "raw-data";
        String processedTopic = "processed-data";

        // Start stream processor in background
        ExecutorService executor = Executors.newSingleThreadExecutor();
        executor.submit(() -> pipeline.processStream(sourceTopic, processedTopic));

        // Produce messages
        pipeline.produceMessages(sourceTopic, 20);

        // Wait for processing
        Thread.sleep(3000);

        // Consume processed messages
        pipeline.consumeMessages(processedTopic, "consumer-group", 20);

        executor.shutdown();
        executor.awaitTermination(5, TimeUnit.SECONDS);
    }
}
