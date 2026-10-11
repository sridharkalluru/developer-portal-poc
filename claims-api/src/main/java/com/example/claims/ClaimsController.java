package com.example.claims;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/api/claims")
public class ClaimsController {
    private final AtomicLong sequence = new AtomicLong(1001);
    private final List<Claim> claims = new CopyOnWriteArrayList<>(
        List.of(new Claim("CLM-1000", "OPEN", "Windshield damage"))
    );

    @GetMapping
    public List<Claim> list() {
        return claims;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Claim create(@RequestBody NewClaim request) {
        Claim claim = new Claim("CLM-" + sequence.getAndIncrement(), "OPEN", request.description());
        claims.add(claim);
        return claim;
    }

    public record Claim(String id, String status, String description) {}
    public record NewClaim(String description) {}
}
