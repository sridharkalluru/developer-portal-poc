package com.example.claims;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ClaimsControllerTest {
    @Autowired MockMvc mvc;

    @Test
    void listClaimsReturnsSeedClaim() throws Exception {
        mvc.perform(get("/api/claims"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$", hasSize(1)))
            .andExpect(jsonPath("$[0].id", is("CLM-1000")))
            .andExpect(jsonPath("$[0].status", is("OPEN")));
    }

    @Test
    void createClaimReturnsCreatedClaim() throws Exception {
        mvc.perform(post("/api/claims")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"description\":\"POC test claim\"}"))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id", is("CLM-1001")))
            .andExpect(jsonPath("$.status", is("OPEN")))
            .andExpect(jsonPath("$.description", is("POC test claim")));
    }
}
