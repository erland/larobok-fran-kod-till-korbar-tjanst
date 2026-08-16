package se.erland.taskboard.task;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.persistence.EntityManager;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@ApplicationScoped
public class TaskRepository {
    @Inject
    EntityManager entityManager;

    public List<TaskEntity> list(TaskStatus status, TaskPriority priority) {
        return entityManager.createQuery(
                        """
                        select t from TaskEntity t
                        where (:status is null or t.status = :status)
                          and (:priority is null or t.priority = :priority)
                        order by t.createdAt desc
                        """, TaskEntity.class)
                .setParameter("status", status)
                .setParameter("priority", priority)
                .getResultList();
    }

    public Optional<TaskEntity> find(UUID id) {
        return Optional.ofNullable(entityManager.find(TaskEntity.class, id));
    }

    public void persist(TaskEntity entity) {
        entityManager.persist(entity);
    }

    public void delete(TaskEntity entity) {
        entityManager.remove(entity);
    }
}
