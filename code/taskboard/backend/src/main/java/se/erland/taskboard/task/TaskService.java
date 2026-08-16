package se.erland.taskboard.task;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import jakarta.ws.rs.NotFoundException;

import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.UUID;

import static se.erland.taskboard.task.TaskDtos.SaveTaskRequest;
import static se.erland.taskboard.task.TaskDtos.TaskResponse;

@ApplicationScoped
public class TaskService {
    @Inject
    TaskRepository repository;

    public List<TaskResponse> list(TaskStatus status, TaskPriority priority) {
        return repository.list(status, priority).stream().map(TaskResponse::from).toList();
    }

    public TaskResponse get(UUID id) {
        return TaskResponse.from(required(id));
    }

    @Transactional
    public TaskResponse create(SaveTaskRequest request) {
        var now = OffsetDateTime.now(ZoneOffset.UTC);
        var entity = new TaskEntity();
        entity.title = request.title().trim();
        entity.description = normalize(request.description());
        entity.status = request.status() == null ? TaskStatus.OPEN : request.status();
        entity.priority = request.priority() == null ? TaskPriority.NORMAL : request.priority();
        entity.dueDate = request.dueDate();
        entity.createdAt = now;
        entity.updatedAt = now;
        repository.persist(entity);
        return TaskResponse.from(entity);
    }

    @Transactional
    public TaskResponse update(UUID id, SaveTaskRequest request) {
        var entity = required(id);
        entity.title = request.title().trim();
        entity.description = normalize(request.description());
        entity.status = request.status() == null ? entity.status : request.status();
        entity.priority = request.priority() == null ? entity.priority : request.priority();
        entity.dueDate = request.dueDate();
        entity.updatedAt = OffsetDateTime.now(ZoneOffset.UTC);
        return TaskResponse.from(entity);
    }

    @Transactional
    public void delete(UUID id) {
        repository.delete(required(id));
    }

    private TaskEntity required(UUID id) {
        return repository.find(id).orElseThrow(NotFoundException::new);
    }

    private String normalize(String value) {
        return value == null || value.isBlank() ? null : value.trim();
    }
}
