// === WebSocketConfig.java ===
package com.example.chat;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.*;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/chat").setAllowedOrigins("*").withSockJS();
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        config.enableSimpleBroker("/topic");
        config.setApplicationDestinationPrefixes("/app");
    }
}

// === ChatMessage.java ===
package com.example.chat;

public class ChatMessage {
    private String sender;
    private String content;
    private String room;
    private String type; // JOIN, CHAT, LEAVE

    // Getters and Setters
    public String getSender() { return sender; }
    public void setSender(String sender) { this.sender = sender; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public String getRoom() { return room; }
    public void setRoom(String room) { this.room = room; }
    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
}

// === ChatController.java ===
package com.example.chat;

import org.springframework.messaging.handler.annotation.*;
import org.springframework.messaging.simp.SimpMessageHeaderAccessor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;
import java.util.*;

@Controller
public class ChatController {
    
    private final SimpMessagingTemplate template;
    private final Map<String, Set<String>> roomUsers = new ConcurrentHashMap<>();

    public ChatController(SimpMessagingTemplate template) {
        this.template = template;
    }

    @MessageMapping("/send")
    public void sendMessage(ChatMessage message) {
        template.convertAndSend("/topic/room/" + message.getRoom(), message);
    }

    @MessageMapping("/join")
    public void joinRoom(ChatMessage message, SimpMessageHeaderAccessor headerAccessor) {
        headerAccessor.getSessionAttributes().put("room", message.getRoom());
        headerAccessor.getSessionAttributes().put("user", message.getSender());

        roomUsers.computeIfAbsent(message.getRoom(), k -> ConcurrentHashMap.newKeySet())
                 .add(message.getSender());

        message.setType("JOIN");
        message.setContent(message.getSender() + " joined the room");
        template.convertAndSend("/topic/room/" + message.getRoom(), message);
        updateUserList(message.getRoom());
    }

    @MessageMapping("/leave")
    public void leaveRoom(ChatMessage message) {
        Set<String> users = roomUsers.get(message.getRoom());
        if (users != null) {
            users.remove(message.getSender());
        }
        message.setType("LEAVE");
        message.setContent(message.getSender() + " left the room");
        template.convertAndSend("/topic/room/" + message.getRoom(), message);
        updateUserList(message.getRoom());
    }

    private void updateUserList(String room) {
        ChatMessage update = new ChatMessage();
        update.setType("USERS");
        update.setRoom(room);
        update.setContent("Online users: " + String.join(", ", roomUsers.getOrDefault(room, Set.of())));
        template.convertAndSend("/topic/room/" + room, update);
    }
}

// Frontend: HTML + SockJS client
// const socket = new SockJS('http://localhost:8080/chat');
// const stompClient = Stomp.over(socket);
// stompClient.connect({}, () => {
//   stompClient.subscribe('/topic/room/general', (msg) => {
//     console.log(JSON.parse(msg.body));
//   });
// });
