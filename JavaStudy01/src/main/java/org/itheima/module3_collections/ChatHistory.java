package org.itheima.module3_collections;

import java.util.ArrayList;
import java.util.List;
/**
 * 滑动窗口：缓存消息
 */
public class ChatHistory {
    //
//    private final List<String> chatHistory = new ArrayList<>();
    private static final int SIZE = 5;
//    List<String> ChatHistory = new ArrayList<>();
    private List<String> chatHistory;
    public ChatHistory() {
        chatHistory = new ArrayList<>();
    }
    public void addMessages(String message) {
        if (chatHistory.size() < SIZE) {
            chatHistory.add(message);
        } else {
            chatHistory.remove(0);
            chatHistory.add(message);
        }
    }
    public void getMessage() {
        for (int i = 0; i < chatHistory.size(); i++) {
            System.out.println(chatHistory.get(i));
        }
    }



    public static void main(String[] args) {
        PromptManager pm =new PromptManager();
//        String output1 = pm.generatePrompt("translate","你是谁");
//        System.out.println(output1);
//        String output2 = pm.generatePrompt("sing","jay zhou style");
//        System.out.println(output2);
//        pm.addPrompt("sing","jay zhou style");
//        String output3 = pm.generatePrompt("sing","jay");
//        System.out.println(output3);
//
//        pm.printLogs();
        List<String> contents = new ArrayList<>();
        contents.add("1");
        contents.add("2");
        contents.add("3");
        contents.add("4");
        contents.add("5");
        contents.add("6");
        contents.add("7");
        contents.add("8");
        ChatHistory history = new ChatHistory();
        for (int m = 0; m < contents.size(); m++){
            history.addMessages(contents.get(m));
            history.getMessage();
//            System.out.println(text);

        }
    }
}
