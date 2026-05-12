package br.ufpb.dsc.cirurgias.controller;

import br.ufpb.dsc.cirurgias.domain.Medico;
import br.ufpb.dsc.cirurgias.repository.MedicoRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/medicos")
public class MedicoController {
    @Autowired
    private MedicoRepository repository;

    @GetMapping
    public List<Medico> listar() {
        return repository.findAll();
    }

    @PostMapping
    public Medico criar(@RequestBody Medico entity) {
        return repository.save(entity);
    }

    @GetMapping("/{id}")
    public Medico buscar(@PathVariable Long id) {
        return repository.findById(id).orElse(null);
    }

    @PutMapping("/{id}")
    public Medico atualizar(@PathVariable Long id, @RequestBody Medico entity) {
        entity.setId(id);
        return repository.save(entity);
    }

    @DeleteMapping("/{id}")
    public void deletar(@PathVariable Long id) {
        repository.deleteById(id);
    }
}
