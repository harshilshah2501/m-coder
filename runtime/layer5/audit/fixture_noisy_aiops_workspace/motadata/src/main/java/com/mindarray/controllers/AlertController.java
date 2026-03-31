package com.mindarray.controllers;

import com.mindarray.aiops.correlation.AlertCorrelationEngine;
import com.mindarray.aiops.correlation.CorrelationService;

@RestController
@RequestMapping("/api/alerts")
public class AlertController {
    
    private final AlertCorrelationEngine correlationEngine;
    private final CorrelationService correlationService;
    
    @GetMapping("/{id}")
    public Alert getAlert(String id) {
        return alertRepository.findById(id);
    }
    
    @PostMapping("/correlate")
    public void correlateAlerts(CorrelationRequest request) {
        correlationEngine.correlateDuplicateIncidents();
        correlationService.correlateAlerts();
    }
    
    @DeleteMapping("/{id}")
    public void deleteAlert(String id) {
        alertRepository.delete(id);
    }
}
