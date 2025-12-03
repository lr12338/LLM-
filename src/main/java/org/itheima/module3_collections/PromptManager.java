package org.itheima.module3_collections;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

public class PromptManager {
    //1.定义成员变量 ： Map 存储模板，Key 是场景名，Value 是模板内容
    //Privete 修饰，体现封装
    private Map<String, String> templates;
    //list 记录调用日志
    private List<String> queryLogs;

    //2.构造方法：初始化容器
    public PromptManager() {
        templates = new HashMap<>();
        queryLogs = new ArrayList<>();

        templates.put("translate","以下内容翻译： {content}");
        templates.put("write","write a song： {content}");
    }
    //3.添加新模板
    public void addTemplate(String template, String content) {
        templates.put(template,content);
    }
    //4.生成最终Prompt
    //scene 生成场景 ”translate“
    //content 输入内容
    public String getPrompt(String scene, String content){
        //1.检查模板是否存在
        if(!templates.containsKey(scene)){
            return "error,无效scene";
        }
        //2.取出模板
        String template = templates.get(scene);
        //3.content替代占位符
        String finalPrompt = template.replace("{content}", content);
        //4.记录日志
        queryLogs.add("场景{"+scene+"}："+finalPrompt);

        return finalPrompt;
    }

    //5.方法：打印日志
    public void printLogs(){
        System.out.println("对话日志：");
        for(int m =0 ;m < queryLogs.size(); m++) {
            System.out.println(queryLogs.get(m));
        }
    }

    //6.方法测试
    public static void main(String[] args) {
        PromptManager pm = new PromptManager();

        //预设模板1
        String output1 = pm.getPrompt("write","jay zhou Style");
        System.out.println(output1);
        String output2 = pm.getPrompt("sing","jay zhou Style");
        System.out.println(output2);
        pm.addTemplate("sing","sing sing sing");
        String output3 = pm.getPrompt("sing","jay zhou Style");
        System.out.println(output3);

        pm.printLogs();
    }


}
