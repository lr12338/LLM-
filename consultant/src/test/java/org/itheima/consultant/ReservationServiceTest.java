package org.itheima.consultant;

import org.itheima.consultant.mapper.ReservationMapper;
import org.itheima.consultant.pojo.Reservation;
import org.itheima.consultant.service.ReservationService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.time.LocalDateTime;

@SpringBootTest
public class ReservationServiceTest {
    @Autowired
    private ReservationService reservationService;
    //测试添加
    @Test
    void testInsert(){
        Reservation reservation = new Reservation(1,"wang","男","1388080808", LocalDateTime.now(),"ANhui",680);
        reservationService.insert(reservation);
    }

    //测试查询
}
