package com.mindarray.schedulers;

import com.mindarray.store.TopologyCacheStore;
import com.mindarray.nms.MetricPoller;

public class MaintenanceScheduler {
    
    private final TopologyCacheStore cacheStore;
    private final MetricPoller metricPoller;
    
    @Scheduled(cron = "0 0 * * * ?")
    public void runDailyMaintenance() {
        cacheStore.cleanup();
        metricPoller.reset();
    }
    
    @Scheduled(fixedRate = 60000)
    public void runMetricCollection() {
        metricPoller.poll();
    }
}
