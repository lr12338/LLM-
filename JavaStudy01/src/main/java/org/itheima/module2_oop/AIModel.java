package org.itheima.module2_oop;

public class AIModel {
    //1.私有属性，外部不可见
    private String name;
    private double temperature;

    //2.构造方法
    //无void的是「构造方法」：它是一种特殊方法，专门用于「创建对象时初始化属性」，没有返回值类型
    public AIModel(String name, double temperature) {
        this.name = name;//this：Java 关键字，指代「当前对象」 在成员变量和局部变量同名时，给当前对象的成员变量赋值。
        this.temperature = temperature;
    }

    /**
     * java 的 构造方法」：它是一种特殊方法，专门用于「创建对象时初始化属性」，没有返回值类型
     * Java 中所有「普通方法」（非构造方法）必须声明「返回值类型」，规则如下：
     * 若方法 不返回任何数据（只执行逻辑，比如 setTemperature），返回值类型写 void；
     * 若方法 需要返回数据（比如 getName 要返回对象的 name 属性），返回值类型必须写「数据的类型」（比如 String、int、double 等），此时不能写 void。
     */
    //3.公开方法（Getter/Setter：控制对属性的访问）
    public String getName() {
        return name;
    }

    //带void的是「普通方法」：void表示 “该方法没有返回值”（只执行逻辑，不返回任何数据）
    public void setTemperature(double temperature) {
        //可业务逻辑校验
        if (temperature < 0.0 || temperature > 1.0) {
            System.out.println("温度必须在0.0至1.0间");
        } else  {
            this.temperature = temperature;
        }
    }
    public void describe(){
        System.out.println("模型"+name+"\n温度："+temperature);
    }
}
