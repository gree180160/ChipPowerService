-- ============================================================================
-- t_ppn_result 宽表 DDL(最终版本)
-- 预计算 PPN 相关的所有指标,支持 SQL 层直接筛选
-- 注意:数值字段统一用 varchar 存储,筛选时后端用 CAST 转数值比较
-- ============================================================================

-- 删除已存在的表(如果需要重建)
DROP TABLE IF EXISTS t_ppn_result;

-- 创建宽表(字段顺序与最终表结构一致)
CREATE TABLE t_ppn_result (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    ppn VARCHAR(100) NOT NULL COMMENT 'PPN 型号',
    manu_name VARCHAR(100) NULL COMMENT '制造商名称',
    digikey_status VARCHAR(50) NULL COMMENT 'DigiKey 状态',
    hq_m_avg VARCHAR(20) NULL COMMENT '华强电子网 月搜索量均值',
    hq_sup_count VARCHAR(13) NULL COMMENT '华强电子网 供给记录数',
    hq_stock VARCHAR(13) NOT NULL DEFAULT '' COMMENT '华强网库存',
    ic_sup_count VARCHAR(13) NULL COMMENT 'IC交易网 供给记录数',
    ic_stock VARCHAR(13) NOT NULL DEFAULT '' COMMENT 'IC交易网库存',
    efind_all_sup VARCHAR(13) NULL DEFAULT '',
    wheat_global VARCHAR(13) NULL COMMENT 'Wheat 全球供给数',
    wheat_ru VARCHAR(13) NULL COMMENT 'Wheat 俄罗斯供给数',
    oc_price VARCHAR(20) NULL COMMENT 'Octopart 最低价格',
    oc_stock VARCHAR(13) NULL DEFAULT '',
    task_name VARCHAR(100) NULL COMMENT '来源任务名',
    update_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
    -- 唯一索引:保证每个 ppn + manu_name + task_name 唯一
    UNIQUE KEY uk_ppn_manu_task (ppn, manu_name, task_name),
    -- 索引:用于筛选查询
    INDEX idx_hq_m_avg (hq_m_avg),
    INDEX idx_hq_sup_count (hq_sup_count),
    INDEX idx_task_name (task_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='PPN 综合指标结果表';
