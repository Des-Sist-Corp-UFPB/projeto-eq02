package br.ufpb.dsc.cirurgias.controller;

import br.ufpb.dsc.cirurgias.domain.TipoCirurgia;
import br.ufpb.dsc.cirurgias.repository.TipoCirurgiaRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/tipocirurgias")
public class TipoCirurgiaController {
    @Autowired
    private TipoCirurgiaRepository repository;

    @GetMapping
    public List<TipoCirurgia> listar() {
        return repository.findAll();
    }

    @PostMapping
    public TipoCirurgia criar(@RequestBody TipoCirurgia entity) {
        return repository.save(entity);
    }

    @GetMapping("/{id}")
    public TipoCirurgia buscar(@PathVariable Long id) {
        return repository.findById(id).orElse(null);
    }

    @PutMapping("/{id}")
    public TipoCirurgia atualizar(@PathVariable Long id, @RequestBody TipoCirurgia entity) {
        entity.setId(id);
        return repository.save(entity);
    }

    @DeleteMapping("/{id}")
    public void deletar(@PathVariable Long id) {
        repository.deleteById(id);
    }
}
