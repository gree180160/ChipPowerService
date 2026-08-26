-- 用户收藏 PPN 表
-- 存储 user_id 对 ppn_id(t_ppn_result.id) 的收藏记录
-- 字段说明:
--   id          自增主键
--   ppn_id      当前 PPN 记录 id (关联 t_ppn_result.id)
--   user_id     当前用户 id (关联 t_user.id)
--   note        用户评价
--   create_time 收藏时间

DROP TABLE IF EXISTS t_ppn_store;
CREATE TABLE t_ppn_store (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ppn_id BIGINT NOT NULL COMMENT '当前记录的id (t_ppn_result.id)',
    user_id BIGINT NOT NULL COMMENT '当前用户的id (t_user.id)',
    note VARCHAR(500) NULL COMMENT '用户评价',
    create_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ppn_id_user (ppn_id, user_id),
    INDEX idx_user (user_id),
    INDEX idx_ppn_id (ppn_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
