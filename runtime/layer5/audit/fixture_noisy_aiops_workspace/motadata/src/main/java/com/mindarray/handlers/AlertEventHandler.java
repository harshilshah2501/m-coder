package com.mindarray.handlers;

import com.mindarray.aiops.correlation.AlertCorrelationEngine;
import com.mindarray.eventbus.EventEngine;

public class AlertEventHandler {
    
    private final AlertCorrelationEngine correlationEngine;
    private final EventEngine eventEngine;
    
    @EventHandler
    public void handle(AlertEvent event) {
        correlationEngine.correlateDuplicateIncidents();
        eventEngine.publish(event);
    }
    
    public void onAlertCreated(AlertCreatedEvent event) {
        correlationEngine.correlateDuplicateIncidents();
    }
}
