package org.itheima.consultant.config;


//import dev.langchain4j.community.store.embedding.redis.RedisEmbeddingStore;
import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.document.DocumentSplitter;
import dev.langchain4j.data.document.loader.ClassPathDocumentLoader;
import dev.langchain4j.data.document.loader.FileSystemDocumentLoader;
import dev.langchain4j.data.document.parser.apache.pdfbox.ApachePdfBoxDocumentParser;
import dev.langchain4j.data.document.splitter.DocumentSplitters;
import dev.langchain4j.memory.ChatMemory;
import dev.langchain4j.memory.chat.ChatMemoryProvider;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.openai.OpenAiChatModel;

import dev.langchain4j.rag.content.retriever.ContentRetriever;
import dev.langchain4j.rag.content.retriever.EmbeddingStoreContentRetriever;
import dev.langchain4j.service.AiServices;
import dev.langchain4j.service.memory.ChatMemoryService;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.EmbeddingStoreIngestor;
import dev.langchain4j.store.embedding.inmemory.InMemoryEmbeddingStore;
import dev.langchain4j.store.memory.chat.ChatMemoryStore;
import org.itheima.consultant.aiservice.ConsultantService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class CommonConfig {

    @Autowired
    private OpenAiChatModel model;
    @Autowired
    private ChatMemoryStore redisChatMemoryService;
    @Autowired
    private EmbeddingModel embeddingModel;
//    @Autowired
//    private RedisEmbeddingStore redisEmbeddingStore;

//    @Bean
//    public ConsultantService consultantService(){
//       ConsultantService consultantService = AiServices.builder(ConsultantService.class)
//                .chatModel(model)
//                .build();
//       return consultantService;
//    }
    //构建会话记忆对象
    @Bean
    public ChatMemory chatMemory(){
        MessageWindowChatMemory memory = MessageWindowChatMemory.builder()
                .maxMessages(20)
                .build();
        return memory;
    }

    //构建ChatMemoryProvider对象
    @Bean
    public ChatMemoryProvider chatMemoryProvider(){
        ChatMemoryProvider chatMemoryProvider = new ChatMemoryProvider() {
            @Override
            public ChatMemory get(Object memoryId) {
                return MessageWindowChatMemory.builder()
                            .id(memoryId)
                            .maxMessages(20)
                            .chatMemoryStore(redisChatMemoryService)
                            .build();
            }
        };
        return chatMemoryProvider;
    }

    //构建向量数据库操作对象
    //只需处理一次，可注释@Bean
    //@Bean
    public EmbeddingStore store(){//加载时会自动创建embeddingStore的对象，不可重复，所以使用 store
        //1.加载文档进内存
        // 文档加载器： FileSystemDocumentLoader，根据本地磁盘绝对路径加载；ClassPathDocumentLoader，相对于类路径加载；UrlDocumentLoader，根据url路径加载
        //文档解析器：
        //List<Document> documents = ClassPathDocumentLoader.loadDocuments("content");
//        List<Document> documents = FileSystemDocumentLoader.loadDocuments("/Users/raymondlu/IdeaProjects/consultant/src/main/resources/content");
        List<Document> documents = ClassPathDocumentLoader.loadDocuments("content",new ApachePdfBoxDocumentParser());
        //2.构建向量数据库操作对象 操作的是内存版本的向量数据库
        InMemoryEmbeddingStore store = new InMemoryEmbeddingStore();

        //构建文档分割器对象
        DocumentSplitter ds = DocumentSplitters.recursive(500,100);
        //3.构建一个EmbeddingStoreIngestor对象，完成文本数据切割、向量化，存储
        EmbeddingStoreIngestor ingestor = EmbeddingStoreIngestor.builder()
                .embeddingStore(store)
//                .embeddingStore(redisEmbeddingStore)
                .documentSplitter(ds)
                .embeddingModel(embeddingModel)
                .build();
        ingestor.ingest(documents);
        return /*redisEmbeddingStore*/store;
    }

    //构建向量数据库检索对象
    @Bean
    public ContentRetriever contentRetriever(/*RedisEmbeddingStore redisEmbeddingStore*/EmbeddingStore store){
        return  EmbeddingStoreContentRetriever.builder()
                    .embeddingStore(store)
//                    .embeddingStore(redisEmbeddingStore)
                    .minScore(0.5)
                    .maxResults(3)
                    .embeddingModel(embeddingModel)
                    .build();
    }
}
