package se.erland.taskboard.task;

import jakarta.inject.Inject;
import jakarta.validation.Valid;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.net.URI;
import java.util.List;
import java.util.UUID;

import static se.erland.taskboard.task.TaskDtos.SaveTaskRequest;
import static se.erland.taskboard.task.TaskDtos.TaskResponse;

@Path("/api/tasks")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class TaskResource {
    @Inject
    TaskService service;

    @GET
    public List<TaskResponse> list(
            @QueryParam("status") TaskStatus status,
            @QueryParam("priority") TaskPriority priority) {
        return service.list(status, priority);
    }

    @GET
    @Path("/{id}")
    public TaskResponse get(@PathParam("id") UUID id) {
        return service.get(id);
    }

    @POST
    public Response create(@Valid SaveTaskRequest request) {
        var created = service.create(request);
        return Response.created(URI.create("/api/tasks/" + created.id())).entity(created).build();
    }

    @PUT
    @Path("/{id}")
    public TaskResponse update(@PathParam("id") UUID id, @Valid SaveTaskRequest request) {
        return service.update(id, request);
    }

    @DELETE
    @Path("/{id}")
    public Response delete(@PathParam("id") UUID id) {
        service.delete(id);
        return Response.noContent().build();
    }
}
