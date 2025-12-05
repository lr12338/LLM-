package org.itheima.consultant.service;

import org.itheima.consultant.mapper.ReservationMapper;
import org.itheima.consultant.pojo.Reservation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ReservationService {
    @Autowired
    private ReservationMapper reservationMapper;

    //1.添加预约信息
    public void insert(Reservation reservation){
        reservationMapper.insert(reservation);
    }
    //2.查询预约信息
    public Reservation findByPhone(String phone){
        return  reservationMapper.findByPhone(phone);
    }
}
