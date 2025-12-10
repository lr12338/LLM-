package com.ray.javastudy02.service;


import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.ray.javastudy02.model.openai.LlmRequest;
import com.ray.javastudy02.model.openai.Message;
import okhttp3.*;
//import okhttp3.OkHttpClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
//import java.sql.Time;
import java.util.Collections;
import java.util.concurrent.TimeUnit;

// 导入 流式输出 需要的包
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Service
public class LlmService {
    //1. 读取配置文件
    @Value("${ai.active.provider}")
    private String activeProvider;

    @Value("${ai.huoshan.url}")
    private String huoshanUrl;
    @Value("${ai.huoshan.key}")
    private String huoshanKey;
    @Value("${ai.huoshan.model}")
    private String huoshanModel;

    @Value("${ai.deepseek.url}")
    private String deepseekUrl;
    @Value("${ai.deepseek.key}")
    private String deepseekKey;
    @Value("${ai.deepseek.model}")
    private String deepseekModel;

    // HTTP 客户端 （设置超时时间为60秒）
    private final OkHttpClient client = new OkHttpClient.Builder()
            .connectTimeout(60, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .build();

    // JSON 解析工具
    private final ObjectMapper objectMapper = new ObjectMapper();

    //1.创建进程池，专门用于执行流式任务，防止阻塞子进程
    private final ExecutorService executorService = Executors.newCachedThreadPool();

    /**
     * 核心方法：调用大模型
     */
    public String callAI(String prompt) throws IOException{
        //1.确定模型
        String apiUrl;
        String apiKey;
        String modelName;
        if (activeProvider.equals("huoshan")){
            apiUrl = huoshanUrl;
            apiKey = huoshanKey;
            modelName = huoshanModel;
        } else {
            apiUrl = deepseekUrl;
            apiKey = deepseekKey;
            modelName = deepseekModel;
        }
        System.out.println("正在调用模型：" + modelName);
//        String name = "deepseek-reasoner";
        //2.构建请求体
        LlmRequest requestPayload  = LlmRequest.builder()
                .model(modelName)
//                .model(name)
                .messages(Collections.singletonList(new Message("user", prompt)))
                .stream(false)
                .temperature(0.7)
                .build();
        String jsonBody = objectMapper.writeValueAsString(requestPayload);

        //3.构建HTTP请求
        RequestBody body = RequestBody.create(jsonBody, MediaType.get("application/json; charset=utf-8"));
        Request request = new Request.Builder()
                .url(apiUrl)
                .header("Authorization", "Bearer " + apiKey) // 关键：身份认证
                .header("Content-Type", "application/json")
                .post(body)
                .build();

        //4.发送请求并获取响应
        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("API 调用失败: " + response.code() + " " + response.message());
            }

            //5.解析响应结果
            //原始响应是复杂的 JSON， 提取 choice[0].message.content
            String responseString = response.body().string();
            JsonNode rootNode = objectMapper.readTree(responseString);

            //路径解析
            String answer = rootNode.path("choices").get(0).path("message").path("content").asText();
            return answer;
        }

    }

    /**
     * 流式调用
     * @param prompt 用户问题
     * @return SseEmitter 发射器对象
     */
    public SseEmitter streamAI(String prompt){
        //1.创建发射器 (设置超时时间为无限，或者长一点，比如 5分钟)
        SseEmitter emitter = new SseEmitter(5 * 60 * 1000L);

        System.out.println("1️⃣ 主线程：已创建 Emitter，准备提交异步任务..."); // [Log 1]

        //2.异步执行 (关键！不能在 Controller 主线程里卡死)
        executorService.execute(() -> {
            System.out.println("2️⃣ 子线程：开始执行..."); // [Log 2]
            try {
                //3.准备配置
                String apiUrl = "huoshan".equals(activeProvider) ? huoshanUrl : deepseekUrl;
                String apiKey = "huoshan".equals(activeProvider) ? huoshanKey : deepseekKey;
                String modelName = "huoshan".equals(activeProvider) ? huoshanModel : deepseekModel;

                System.out.println("3️⃣ 配置加载完成，Provider: " + activeProvider + ", URL: " + apiUrl); // [Log 3]

                //4.构建请求
                LlmRequest requestPayload  = LlmRequest.builder()
                        .model(modelName)
                        .messages(Collections.singletonList(new Message("user", prompt)))
                        .stream(true) //流式
                        .temperature(0.7)
                        .build();

                String jsonBody = objectMapper.writeValueAsString(requestPayload);

                System.out.println("4️⃣ 请求体已构建，准备发送 HTTP 请求..."); // [Log 4]


                Request request = new Request.Builder()
                        .url(apiUrl)
                        .header("Authorization", "Bearer " + apiKey)
                        .header("Content-Type", "application/json")
                        .post(RequestBody.create(jsonBody, MediaType.get("application/json")))
                        .build();

                //5.发送请求并获取 “流”
                try(Response response = client.newCall(request).execute()){

                    System.out.println("5️⃣ HTTP 响应状态码: " + response.code()); // [Log 5]

                    if (!response.isSuccessful()) {

                        System.out.println("❌ API 调用失败: " + response.body().string()); // 打印错误详情

                        emitter.send("Error: API Error " + response.code());
                        emitter.complete();
                        return;
                    }

                    // 获取字节流
                    InputStream inputStream = response.body().byteStream();
                    BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
                    String line;

                    System.out.println("6️⃣ 开始读取流..."); // [Log 6]


                    // 6. 逐行读取 (AI 返回的数据格式通常是 data: {...JSON...})
                    while ((line = reader.readLine()) != null) {

                        System.out.println("收到原始行: " + line); // 调试时可以打开，看原始数据

                        if (line.isEmpty()) continue; // 跳过空行
                        if (line.equals("data: [DONE]")) {
                            // 结束标志
                            break;
                        }
                        if (line.startsWith("data: ")) {
                            // 去掉前缀 "data: "，拿到真正的 JSON
                            String jsonPart = line.substring(6);

                            try {
                                // 解析 JSON
                                JsonNode node = objectMapper.readTree(jsonPart);
                                // 提取内容: choices[0].delta.content (注意流式里叫 delta，不是 message)
                                if (node.has("choices") && node.get(0).has("delta")) {
                                    JsonNode delta = node.get(0).get("delta");
                                    if (delta.has("content")) {
                                        String content = delta.get("content").asText();

                                        // 🛠️ 关键调试日志：确认到底有没有提取到？
                                        System.out.println("✅ 提取成功，准备发送: [" + content + "]");

                                        // 发送数据 (为了防止编码问题，指定为纯文本)
                                        emitter.send(content, org.springframework.http.MediaType.TEXT_PLAIN);
                                }
                            } }catch (Exception e) {
                                // 忽略解析错误的行
                            }
                        }
                    }

                    System.out.println("\n7️⃣ 流读取结束"); // [Log 7]
                    // 循环结束，告诉前端：完事了
                    emitter.complete();
                }

            } catch (Exception e) {

                System.out.println("❌❌❌ 子线程发生异常: "); // [Log Error]
                e.printStackTrace(); // 必须打印堆栈！

                emitter.completeWithError(e);
            }
        });

        return emitter;

    }

}
