package br.ufpb.dsc.cirurgias.controller;

import br.ufpb.dsc.cirurgias.domain.Cirurgia;
import br.ufpb.dsc.cirurgias.repository.CirurgiaRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/cirurgias")
public class CirurgiaController {
    @Autowired
    private CirurgiaRepository repository;

    @GetMapping
    public List<Cirurgia> listar() {
        return repository.findAll();
    }

    @PostMapping
    public Cirurgia criar(@RequestBody Cirurgia entity) {
        return repository.save(entity);
    }

    @GetMapping("/{id}")
    public Cirurgia buscar(@PathVariable Long id) {
        return repository.findById(id).orElse(null);
    }

    @PutMapping("/{id}")
    public Cirurgia atualizar(@PathVariable Long id, @RequestBody Cirurgia entity) {
        entity.setId(id);
        return repository.save(entity);
    }

    @DeleteMapping("/{id}")
    public void deletar(@PathVariable Long id) {
        repository.deleteById(id);
    }
}
