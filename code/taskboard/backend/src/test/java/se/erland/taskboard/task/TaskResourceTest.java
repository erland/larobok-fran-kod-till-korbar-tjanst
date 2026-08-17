package se.erland.taskboard.task;

import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.endsWith;
import static org.hamcrest.CoreMatchers.equalTo;
import static org.hamcrest.CoreMatchers.hasItem;
import static org.hamcrest.CoreMatchers.not;
import static org.hamcrest.CoreMatchers.nullValue;
import static org.hamcrest.Matchers.emptyOrNullString;

@QuarkusTest
class TaskResourceTest {

    @Test
    void createListUpdateAndDeleteTask() {
        String title = "API test " + UUID.randomUUID();

        var createResponse = given()
                .contentType("application/json")
                .body("""
                        {
                          "title": "  %s  ",
                          "description": "   ",
                          "status": "OPEN",
                          "priority": "HIGH",
                          "dueDate": "2026-09-01"
                        }
                        """.formatted(title))
                .when()
                .post("/api/tasks");

        createResponse.then()
                .statusCode(201)
                .body("title", equalTo(title))
                .body("description", nullValue())
                .body("status", equalTo("OPEN"))
                .body("priority", equalTo("HIGH"))
                .body("dueDate", equalTo("2026-09-01"))
                .body("createdAt", not(emptyOrNullString()))
                .body("updatedAt", not(emptyOrNullString()));

        String id = createResponse.jsonPath().getString("id");
        createResponse.then().header("Location", endsWith("/api/tasks/" + id));

        given()
                .queryParam("status", "OPEN")
                .queryParam("priority", "HIGH")
                .when()
                .get("/api/tasks")
                .then()
                .statusCode(200)
                .body("id", hasItem(id));

        given()
                .when()
                .get("/api/tasks/{id}", id)
                .then()
                .statusCode(200)
                .body("id", equalTo(id))
                .body("title", equalTo(title));

        given()
                .contentType("application/json")
                .body("""
                        {
                          "title": "Updated task",
                          "description": "Updated through the API test",
                          "status": "DONE",
                          "priority": "LOW",
                          "dueDate": null
                        }
                        """)
                .when()
                .put("/api/tasks/{id}", id)
                .then()
                .statusCode(200)
                .body("id", equalTo(id))
                .body("title", equalTo("Updated task"))
                .body("description", equalTo("Updated through the API test"))
                .body("status", equalTo("DONE"))
                .body("priority", equalTo("LOW"))
                .body("dueDate", nullValue());

        given()
                .when()
                .delete("/api/tasks/{id}", id)
                .then()
                .statusCode(204);

        given()
                .when()
                .get("/api/tasks/{id}", id)
                .then()
                .statusCode(404);
    }

    @Test
    void rejectsBlankTitle() {
        given()
                .contentType("application/json")
                .body("""
                        {
                          "title": "   ",
                          "status": "OPEN",
                          "priority": "NORMAL"
                        }
                        """)
                .when()
                .post("/api/tasks")
                .then()
                .statusCode(400);
    }

    @Test
    void rejectsUnsupportedPriority() {
        given()
                .contentType("application/json")
                .body("""
                        {
                          "title": "Regression test",
                          "status": "OPEN",
                          "priority": "MEDIUM"
                        }
                        """)
                .when()
                .post("/api/tasks")
                .then()
                .statusCode(400);
    }

    @Test
    void returnsNotFoundForUnknownTask() {
        given()
                .when()
                .get("/api/tasks/{id}", UUID.randomUUID())
                .then()
                .statusCode(404);
    }

}
