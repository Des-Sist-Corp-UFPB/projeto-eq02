package br.ufpb.dsc.cirurgias.controller;

import br.ufpb.dsc.cirurgias.domain.Hospital;
import br.ufpb.dsc.cirurgias.repository.HospitalRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/hospitals")
public class HospitalController {
    @Autowired
    private HospitalRepository repository;

    @GetMapping
    public List<Hospital> listar() {
        return repository.findAll();
    }

    @PostMapping
    public Hospital criar(@RequestBody Hospital entity) {
        return repository.save(entity);
    }

    @GetMapping("/{id}")
    public Hospital buscar(@PathVariable Long id) {
        return repository.findById(id).orElse(null);
    }

    @PutMapping("/{id}")
    public Hospital atualizar(@PathVariable Long id, @RequestBody Hospital entity) {
        entity.setId(id);
        return repository.save(entity);
    }

    @DeleteMapping("/{id}")
    public void deletar(@PathVariable Long id) {
        repository.deleteById(id);
    }
}
