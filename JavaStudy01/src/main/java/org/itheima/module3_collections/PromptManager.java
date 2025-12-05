package org.itheima.module3_collections;

import java.util.Scanner;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;

public class PromptManager {
    //定义成员变量
    private Map<String, String> template;
    //定义日志变量
    List<String> queryLogs = new ArrayList<>();
    //构造方法：初始化容器
    public PromptManager(){
        template = new HashMap<>();
        template.put("translate", "请翻译这段话： {content}");
        template.put("write", "请撰写一段话： {content}");
    }
    //方法：添加新模板
    public void addPrompt(String key, String value){
        template.put(key,value);
    }
    //方法：生成最终Prompt
    public String generatePrompt(String key,String content){
        if(!template.containsKey(key)){
            return "无效场景 key";
        }
        String prompt = template.get(key);
        String inputContent = prompt.replace("content",content);
        queryLogs.add("场景["+key+"]:回复："+inputContent);
        return "场景["+key+"]:回复："+inputContent;
    }
    //方法：打印日志
    public void printLogs(){
        for (int y = 0; y < queryLogs.size();y++){
            System.out.println(queryLogs.get(y));
        }
    }
    //测试
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
            System.out.println(history);

        }
    }

}
