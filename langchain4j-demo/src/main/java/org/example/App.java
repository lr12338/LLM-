package org.example;

import dev.langchain4j.model.openai.OpenAiChatModel;

/**
 * Hello world!
 *
 */
public class App 
{
    public static void main( String[] args )
    {
//        String apiKey = System.getenv("DEEPSEEK_API_KEY");
//        System.out.println(apiKey);
//        System.out.println( "Hello World!" );
        //2.构建OpenAiChatModel对象
        OpenAiChatModel model = OpenAiChatModel.builder()
                .baseUrl("https://api.deepseek.com")
                //DEEPSEEK_API_KEY="sk-af635e7fa9b448b7be5fedfc9ba5a740"
                .apiKey(System.getenv("DEEPSEEK_API_KEY"))
                // model = deepseek-chat deepseek-reasoner
                .modelName("deepseek-chat")
                //日志
                .logRequests(true)
                .logResponses(true)
                .build();

        //3.调用chat方法，交互
        String result = model.chat("你是谁？");
        System.out.println(result);



    }
}
