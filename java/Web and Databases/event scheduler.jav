// === pom.xml dependencies ===
// quartz, slf4j-simple, h2

// === EmailJob.java ===
package com.example.scheduler;

import org.quartz.*;
import java.time.LocalDateTime;
import java.util.*;

public class EmailJob implements Job {
    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        JobDataMap data = context.getMergedJobDataMap();
        String email = data.getString("email");
        String subject = data.getString("subject");
        String message = data.getString("message");

        System.out.println("[" + LocalDateTime.now() + "] Sending email to: " + email);
        System.out.println("Subject: " + subject);
        System.out.println("Message: " + message);
        
        // Simulate email sending
        try {
            Thread.sleep(500);
            System.out.println("Email sent successfully!");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}

// === SchedulerManager.java ===
package com.example.scheduler;

import org.quartz.*;
import org.quartz.impl.StdSchedulerFactory;
import java.util.*;

public class SchedulerManager {
    private Scheduler scheduler;

    public void initialize() throws SchedulerException {
        scheduler = StdSchedulerFactory.getDefaultScheduler();
        scheduler.start();
        System.out.println("Scheduler started");
    }

    public String scheduleEmail(String email, String subject, String message, String cronExpression) 
            throws SchedulerException {
        JobKey jobKey = JobKey.jobKey("email_job_" + UUID.randomUUID().toString());
        
        JobDetail job = JobBuilder.newJob(EmailJob.class)
            .withIdentity(jobKey)
            .usingJobData("email", email)
            .usingJobData("subject", subject)
            .usingJobData("message", message)
            .build();

        CronTrigger trigger = TriggerBuilder.newTrigger()
            .withSchedule(CronScheduleBuilder.cronSchedule(cronExpression))
            .build();

        scheduler.scheduleJob(job, trigger);
        return jobKey.getName();
    }

    public void scheduleOneTimeEmail(String email, String subject, String message, Date fireTime) 
            throws SchedulerException {
        JobDetail job = JobBuilder.newJob(EmailJob.class)
            .usingJobData("email", email)
            .usingJobData("subject", subject)
            .usingJobData("message", message)
            .build();

        Trigger trigger = TriggerBuilder.newTrigger()
            .startAt(fireTime)
            .build();

        scheduler.scheduleJob(job, trigger);
    }

    public void shutdown() throws SchedulerException {
        if (scheduler != null) {
            scheduler.shutdown();
            System.out.println("Scheduler shutdown");
        }
    }

    public static void main(String[] args) throws Exception {
        SchedulerManager manager = new SchedulerManager();
        manager.initialize();

        // Schedule email every minute
        String jobId = manager.scheduleEmail(
            "user@example.com",
            "Daily Reminder",
            "This is your daily reminder",
            "0 * * * * ?" // Every minute
        );
        System.out.println("Scheduled job: " + jobId);

        // Schedule one-time email in 5 seconds
        Date fireTime = new Date(System.currentTimeMillis() + 5000);
        manager.scheduleOneTimeEmail(
            "alice@example.com",
            "One-time Email",
            "This email was scheduled as a one-time job",
            fireTime
        );
        System.out.println("Scheduled one-time email at: " + fireTime);

        // Keep running for 5 minutes
        Thread.sleep(300000);
        
        manager.shutdown();
    }
}
