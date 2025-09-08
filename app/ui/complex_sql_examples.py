"""Очень сложные примеры SQL запросов для тестирования Explain анализа."""

# Сложные примеры SQL запросов для тестирования Explain анализа
COMPLEX_SQL_EXAMPLES = {
    "Множественные JOIN с подзапросами": """
-- Сложный запрос с множественными JOIN и подзапросами
WITH monthly_stats AS (
    SELECT 
        DATE_TRUNC('month', created_at) as month,
        user_id,
        COUNT(*) as activity_count,
        SUM(amount) as total_amount
    FROM user_activities 
    WHERE created_at >= '2024-01-01'
    GROUP BY DATE_TRUNC('month', created_at), user_id
),
user_rankings AS (
    SELECT 
        user_id,
        month,
        activity_count,
        total_amount,
        ROW_NUMBER() OVER (PARTITION BY month ORDER BY total_amount DESC) as rank
    FROM monthly_stats
)
SELECT 
    u.id,
    u.username,
    u.email,
    ur.month,
    ur.activity_count,
    ur.total_amount,
    ur.rank,
    p.profile_data,
    s.subscription_type,
    s.status as subscription_status
FROM users u
INNER JOIN user_rankings ur ON u.id = ur.user_id
LEFT JOIN user_profiles p ON u.id = p.user_id
LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'active'
WHERE ur.rank <= 10
    AND u.created_at >= '2023-01-01'
    AND u.status = 'active'
ORDER BY ur.month DESC, ur.rank ASC;
""",

    "Агрегация с оконными функциями": """
-- Сложная агрегация с оконными функциями и аналитическими функциями
SELECT 
    department_id,
    employee_id,
    salary,
    LAG(salary, 1) OVER (PARTITION BY department_id ORDER BY salary) as prev_salary,
    LEAD(salary, 1) OVER (PARTITION BY department_id ORDER BY salary) as next_salary,
    AVG(salary) OVER (PARTITION BY department_id) as dept_avg_salary,
    PERCENT_RANK() OVER (PARTITION BY department_id ORDER BY salary) as salary_percentile,
    NTILE(4) OVER (PARTITION BY department_id ORDER BY salary) as salary_quartile,
    COUNT(*) OVER (PARTITION BY department_id) as dept_employee_count,
    SUM(salary) OVER (PARTITION BY department_id ORDER BY salary ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total
FROM employees e
INNER JOIN departments d ON e.department_id = d.id
WHERE e.hire_date >= '2020-01-01'
    AND d.status = 'active'
    AND e.status = 'active'
ORDER BY department_id, salary DESC;
""",

    "Рекурсивный CTE с иерархией": """
-- Рекурсивный CTE для работы с иерархической структурой
WITH RECURSIVE category_hierarchy AS (
    -- Базовый случай: корневые категории
    SELECT 
        id,
        name,
        parent_id,
        0 as level,
        ARRAY[id] as path,
        name as full_path
    FROM categories 
    WHERE parent_id IS NULL
    
    UNION ALL
    
    -- Рекурсивный случай: дочерние категории
    SELECT 
        c.id,
        c.name,
        c.parent_id,
        ch.level + 1,
        ch.path || c.id,
        ch.full_path || ' > ' || c.name
    FROM categories c
    INNER JOIN category_hierarchy ch ON c.parent_id = ch.id
),
product_stats AS (
    SELECT 
        category_id,
        COUNT(*) as product_count,
        AVG(price) as avg_price,
        MIN(price) as min_price,
        MAX(price) as max_price,
        SUM(stock_quantity) as total_stock
    FROM products
    WHERE status = 'active'
    GROUP BY category_id
)
SELECT 
    ch.id,
    ch.name,
    ch.level,
    ch.full_path,
    COALESCE(ps.product_count, 0) as product_count,
    COALESCE(ps.avg_price, 0) as avg_price,
    COALESCE(ps.min_price, 0) as min_price,
    COALESCE(ps.max_price, 0) as max_price,
    COALESCE(ps.total_stock, 0) as total_stock
FROM category_hierarchy ch
LEFT JOIN product_stats ps ON ch.id = ps.category_id
ORDER BY ch.level, ch.name;
""",

    "Сложные подзапросы с EXISTS": """
-- Сложный запрос с EXISTS и множественными подзапросами
SELECT 
    o.id as order_id,
    o.order_date,
    o.total_amount,
    c.customer_name,
    c.email,
    (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id = o.id) as item_count,
    (SELECT SUM(oi.quantity * oi.unit_price) FROM order_items oi WHERE oi.order_id = o.id) as calculated_total,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM order_items oi 
            INNER JOIN products p ON oi.product_id = p.id 
            WHERE oi.order_id = o.id AND p.category = 'electronics'
        ) THEN 'Has Electronics'
        ELSE 'No Electronics'
    END as has_electronics,
    CASE 
        WHEN o.total_amount > (
            SELECT AVG(total_amount) 
            FROM orders 
            WHERE order_date >= o.order_date - INTERVAL '30 days'
        ) THEN 'Above Average'
        ELSE 'Below Average'
    END as amount_vs_average
FROM orders o
INNER JOIN customers c ON o.customer_id = c.id
WHERE o.order_date >= '2024-01-01'
    AND EXISTS (
        SELECT 1 FROM order_items oi 
        WHERE oi.order_id = o.id 
        AND oi.quantity > 1
    )
    AND NOT EXISTS (
        SELECT 1 FROM order_items oi 
        INNER JOIN products p ON oi.product_id = p.id 
        WHERE oi.order_id = o.id 
        AND p.status = 'discontinued'
    )
ORDER BY o.order_date DESC, o.total_amount DESC;
""",

    "Аналитические функции с группировкой": """
-- Сложный аналитический запрос с группировкой и оконными функциями
SELECT 
    region,
    country,
    city,
    product_category,
    SUM(sales_amount) as total_sales,
    COUNT(*) as transaction_count,
    AVG(sales_amount) as avg_sales,
    STDDEV(sales_amount) as sales_stddev,
    -- Оконные функции
    ROW_NUMBER() OVER (PARTITION BY region, country ORDER BY SUM(sales_amount) DESC) as country_rank_in_region,
    RANK() OVER (PARTITION BY region ORDER BY SUM(sales_amount) DESC) as region_rank,
    DENSE_RANK() OVER (ORDER BY SUM(sales_amount) DESC) as global_rank,
    LAG(SUM(sales_amount), 1) OVER (PARTITION BY region, country ORDER BY city) as prev_city_sales,
    LEAD(SUM(sales_amount), 1) OVER (PARTITION BY region, country ORDER BY city) as next_city_sales,
    -- Агрегатные функции в окнах
    SUM(SUM(sales_amount)) OVER (PARTITION BY region) as region_total,
    SUM(SUM(sales_amount)) OVER (PARTITION BY region, country) as country_total,
    SUM(SUM(sales_amount)) OVER () as global_total,
    -- Проценты
    ROUND(100.0 * SUM(sales_amount) / SUM(SUM(sales_amount)) OVER (PARTITION BY region), 2) as pct_of_region,
    ROUND(100.0 * SUM(sales_amount) / SUM(SUM(sales_amount)) OVER (), 2) as pct_of_global
FROM sales_transactions st
INNER JOIN locations l ON st.location_id = l.id
INNER JOIN products p ON st.product_id = p.id
WHERE st.transaction_date >= '2024-01-01'
    AND st.transaction_date < '2024-02-01'
    AND st.status = 'completed'
GROUP BY region, country, city, product_category
HAVING SUM(sales_amount) > 1000
ORDER BY region, country, total_sales DESC;
""",

    "Сложные JOIN с множественными условиями": """
-- Сложный запрос с множественными JOIN и сложными условиями
SELECT 
    p.id as project_id,
    p.name as project_name,
    p.status as project_status,
    p.budget,
    p.start_date,
    p.end_date,
    -- Информация о команде
    COUNT(DISTINCT tm.user_id) as team_size,
    COUNT(DISTINCT CASE WHEN tm.role = 'lead' THEN tm.user_id END) as lead_count,
    COUNT(DISTINCT CASE WHEN tm.role = 'developer' THEN tm.user_id END) as developer_count,
    -- Информация о задачах
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN t.id END) as in_progress_tasks,
    COUNT(CASE WHEN t.status = 'pending' THEN t.id END) as pending_tasks,
    -- Временные метрики
    AVG(CASE WHEN t.status = 'completed' THEN EXTRACT(EPOCH FROM (t.completed_at - t.created_at))/3600 END) as avg_completion_hours,
    MAX(t.due_date) as latest_due_date,
    -- Бюджетные метрики
    SUM(CASE WHEN t.status = 'completed' THEN t.estimated_cost ELSE 0 END) as spent_budget,
    p.budget - SUM(CASE WHEN t.status = 'completed' THEN t.estimated_cost ELSE 0 END) as remaining_budget,
    -- Прогресс
    ROUND(100.0 * COUNT(CASE WHEN t.status = 'completed' THEN t.id END) / NULLIF(COUNT(t.id), 0), 2) as completion_percentage
FROM projects p
LEFT JOIN team_members tm ON p.id = tm.project_id AND tm.status = 'active'
LEFT JOIN tasks t ON p.id = t.project_id
LEFT JOIN users u ON tm.user_id = u.id
WHERE p.created_at >= '2024-01-01'
    AND (p.status = 'active' OR p.status = 'completed')
    AND (t.id IS NULL OR t.created_at >= '2024-01-01')
GROUP BY p.id, p.name, p.status, p.budget, p.start_date, p.end_date
HAVING COUNT(t.id) > 0 OR COUNT(DISTINCT tm.user_id) > 0
ORDER BY completion_percentage DESC, p.start_date DESC;
""",

    "Оптимизация с индексами и статистикой": """
-- Запрос для анализа производительности и оптимизации
SELECT 
    schemaname,
    tablename,
    attname as column_name,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs,
    histogram_bounds,
    CASE 
        WHEN n_distinct = -1 THEN 'All values distinct'
        WHEN n_distinct = 0 THEN 'No distinct values'
        ELSE n_distinct::text
    END as distinct_count,
    CASE 
        WHEN correlation > 0.9 THEN 'High positive correlation'
        WHEN correlation > 0.5 THEN 'Medium positive correlation'
        WHEN correlation > -0.5 THEN 'Low correlation'
        WHEN correlation > -0.9 THEN 'Medium negative correlation'
        ELSE 'High negative correlation'
    END as correlation_level,
    -- Анализ индексов
    (SELECT COUNT(*) FROM pg_indexes WHERE tablename = st.tablename AND schemaname = st.schemaname) as index_count,
    -- Анализ использования
    (SELECT COALESCE(SUM(seq_scan), 0) FROM pg_stat_user_tables WHERE relname = st.tablename) as seq_scans,
    (SELECT COALESCE(SUM(idx_scan), 0) FROM pg_stat_user_tables WHERE relname = st.tablename) as idx_scans
FROM pg_stats st
WHERE schemaname = 'public'
    AND tablename IN (
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    )
    AND n_distinct > 0
ORDER BY 
    CASE 
        WHEN correlation IS NULL THEN 0
        ELSE ABS(correlation)
    END DESC,
    n_distinct DESC;
""",

    "Сложные временные запросы": """
-- Сложный запрос с временными функциями и интервалами
WITH daily_metrics AS (
    SELECT 
        DATE_TRUNC('day', event_timestamp) as event_date,
        user_id,
        event_type,
        COUNT(*) as event_count,
        COUNT(DISTINCT session_id) as unique_sessions,
        MIN(event_timestamp) as first_event,
        MAX(event_timestamp) as last_event,
        EXTRACT(EPOCH FROM (MAX(event_timestamp) - MIN(event_timestamp)))/3600 as session_duration_hours
    FROM user_events
    WHERE event_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY DATE_TRUNC('day', event_timestamp), user_id, event_type
),
user_cohorts AS (
    SELECT 
        user_id,
        DATE_TRUNC('week', MIN(event_timestamp)) as cohort_week,
        COUNT(DISTINCT DATE_TRUNC('day', event_timestamp)) as active_days,
        SUM(event_count) as total_events
    FROM user_events
    WHERE event_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY user_id
),
retention_analysis AS (
    SELECT 
        uc.cohort_week,
        COUNT(DISTINCT uc.user_id) as cohort_size,
        COUNT(DISTINCT CASE WHEN dm.event_date >= uc.cohort_week + INTERVAL '7 days' THEN dm.user_id END) as week_1_retained,
        COUNT(DISTINCT CASE WHEN dm.event_date >= uc.cohort_week + INTERVAL '14 days' THEN dm.user_id END) as week_2_retained,
        COUNT(DISTINCT CASE WHEN dm.event_date >= uc.cohort_week + INTERVAL '21 days' THEN dm.user_id END) as week_3_retained,
        COUNT(DISTINCT CASE WHEN dm.event_date >= uc.cohort_week + INTERVAL '28 days' THEN dm.user_id END) as week_4_retained
    FROM user_cohorts uc
    LEFT JOIN daily_metrics dm ON uc.user_id = dm.user_id
    GROUP BY uc.cohort_week
)
SELECT 
    ra.cohort_week,
    ra.cohort_size,
    ra.week_1_retained,
    ra.week_2_retained,
    ra.week_3_retained,
    ra.week_4_retained,
    ROUND(100.0 * ra.week_1_retained / NULLIF(ra.cohort_size, 0), 2) as week_1_retention_rate,
    ROUND(100.0 * ra.week_2_retained / NULLIF(ra.cohort_size, 0), 2) as week_2_retention_rate,
    ROUND(100.0 * ra.week_3_retained / NULLIF(ra.cohort_size, 0), 2) as week_3_retention_rate,
    ROUND(100.0 * ra.week_4_retained / NULLIF(ra.cohort_size, 0), 2) as week_4_retention_rate
FROM retention_analysis ra
ORDER BY ra.cohort_week DESC;
""",

    "Машинное обучение и статистика": """
-- Сложный запрос для машинного обучения и статистического анализа
WITH user_features AS (
    SELECT 
        user_id,
        -- Временные признаки
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MIN(event_timestamp)))/86400 as days_since_first_event,
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX(event_timestamp)))/86400 as days_since_last_event,
        COUNT(DISTINCT DATE_TRUNC('day', event_timestamp)) as active_days,
        COUNT(DISTINCT DATE_TRUNC('week', event_timestamp)) as active_weeks,
        COUNT(DISTINCT DATE_TRUNC('month', event_timestamp)) as active_months,
        -- Поведенческие признаки
        COUNT(*) as total_events,
        COUNT(DISTINCT event_type) as unique_event_types,
        COUNT(DISTINCT session_id) as unique_sessions,
        AVG(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchase_rate,
        AVG(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as click_rate,
        -- Временные паттерны
        AVG(EXTRACT(HOUR FROM event_timestamp)) as avg_hour_of_day,
        STDDEV(EXTRACT(HOUR FROM event_timestamp)) as hour_stddev,
        -- Сессионные признаки
        AVG(session_duration_seconds) as avg_session_duration,
        STDDEV(session_duration_seconds) as session_duration_stddev
    FROM user_events
    WHERE event_timestamp >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY user_id
),
user_segments AS (
    SELECT 
        user_id,
        days_since_first_event,
        days_since_last_event,
        active_days,
        total_events,
        purchase_rate,
        click_rate,
        avg_session_duration,
        -- Сегментация пользователей
        CASE 
            WHEN days_since_last_event <= 7 AND total_events >= 100 THEN 'Power User'
            WHEN days_since_last_event <= 30 AND total_events >= 50 THEN 'Active User'
            WHEN days_since_last_event <= 90 AND total_events >= 10 THEN 'Occasional User'
            ELSE 'Inactive User'
        END as user_segment,
        -- RFM анализ
        CASE 
            WHEN days_since_last_event <= 7 THEN 5
            WHEN days_since_last_event <= 30 THEN 4
            WHEN days_since_last_event <= 90 THEN 3
            WHEN days_since_last_event <= 180 THEN 2
            ELSE 1
        END as recency_score,
        CASE 
            WHEN total_events >= 100 THEN 5
            WHEN total_events >= 50 THEN 4
            WHEN total_events >= 20 THEN 3
            WHEN total_events >= 5 THEN 2
            ELSE 1
        END as frequency_score,
        CASE 
            WHEN purchase_rate >= 0.1 THEN 5
            WHEN purchase_rate >= 0.05 THEN 4
            WHEN purchase_rate >= 0.02 THEN 3
            WHEN purchase_rate >= 0.01 THEN 2
            ELSE 1
        END as monetary_score
    FROM user_features
)
SELECT 
    user_segment,
    COUNT(*) as user_count,
    AVG(days_since_first_event) as avg_days_since_first,
    AVG(days_since_last_event) as avg_days_since_last,
    AVG(active_days) as avg_active_days,
    AVG(total_events) as avg_total_events,
    AVG(purchase_rate) as avg_purchase_rate,
    AVG(click_rate) as avg_click_rate,
    AVG(avg_session_duration) as avg_session_duration,
    AVG(recency_score) as avg_recency_score,
    AVG(frequency_score) as avg_frequency_score,
    AVG(monetary_score) as avg_monetary_score,
    -- Статистические меры
    STDDEV(total_events) as events_stddev,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_events) as median_events,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_events) as q1_events,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_events) as q3_events
FROM user_segments
GROUP BY user_segment
ORDER BY 
    CASE user_segment
        WHEN 'Power User' THEN 1
        WHEN 'Active User' THEN 2
        WHEN 'Occasional User' THEN 3
        WHEN 'Inactive User' THEN 4
    END;
"""
}

def get_complex_examples():
    """Возвращает словарь сложных примеров SQL запросов."""
    return COMPLEX_SQL_EXAMPLES

def get_example_by_name(name: str) -> str:
    """Возвращает конкретный пример по имени."""
    return COMPLEX_SQL_EXAMPLES.get(name, "")

def get_all_example_names() -> list:
    """Возвращает список всех доступных примеров."""
    return list(COMPLEX_SQL_EXAMPLES.keys())
