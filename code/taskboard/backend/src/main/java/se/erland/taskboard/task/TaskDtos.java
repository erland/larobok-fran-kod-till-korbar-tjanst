package se.erland.taskboard.task;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.UUID;

public final class TaskDtos {
    private TaskDtos() {
    }

    public record SaveTaskRequest(
            @NotBlank @Size(max = 160) String title,
            @Size(max = 4000) String description,
            TaskStatus status,
            TaskPriority priority,
            LocalDate dueDate) {
    }

    public record TaskResponse(
            UUID id,
            String title,
            String description,
            TaskStatus status,
            TaskPriority priority,
            LocalDate dueDate,
            OffsetDateTime createdAt,
            OffsetDateTime updatedAt) {

        static TaskResponse from(TaskEntity entity) {
            return new TaskResponse(
                    entity.id,
                    entity.title,
                    entity.description,
                    entity.status,
                    entity.priority,
                    entity.dueDate,
                    entity.createdAt,
                    entity.updatedAt);
        }
    }
}
