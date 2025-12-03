package org.itheima.module3_collections;

/**
 * HashMap 键值对查找，常用的Map实现，常用于存储配置参数、Prompt模版或缓存
 */
import java.util.Map;
import java.util.HashMap;

public class MapDemo {
    public static void main(String[] args) {
        //Key，Value ：Key String 配置项名字 ； Value Double 数值
        Map<String,Double> config = new HashMap<>();

        //1.增/改 Put
        config.put("temperature",1.0);
        config.put("top_p",0.9);

        //put:若key对应的value已存在，则会覆盖旧值
        config.put("temperature",0.8);

        //2.查 Get
        Double temperature = config.get("temperature");
        System.out.println(temperature);

        //3.判断是否存在 ContainsKey  config.containsKey("")
        if (config.containsKey("api_key")){
            System.out.println(config.get("api_key"));
        } else {
            System.out.println("缺少参数 api_key");
        }

        //4.遍历 for (String key : config.keySet())
        for (String key : config.keySet()) {
            System.out.println(key + ":" + config.get(key));
        }

    }

}
