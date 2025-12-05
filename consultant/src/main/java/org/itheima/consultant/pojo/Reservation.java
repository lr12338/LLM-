package org.itheima.consultant.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Reservation {
        private long id;
        private String name;
        private String gender;
        private String phone;
        private LocalDateTime communicationTime;
        private String province;
        private Integer estimatedScore;
}
