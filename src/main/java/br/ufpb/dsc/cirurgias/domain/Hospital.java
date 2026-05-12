package br.ufpb.dsc.cirurgias.domain;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "hospital")
public class Hospital {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String nome;
    private String endereco;
    
    @Column(name = "criado_em", nullable = false, updatable = false)
    private Instant criadoEm;
    @Column(name = "atualizado_em", nullable = false)
    private Instant atualizadoEm;

    @PrePersist protected void prePersist() { criadoEm = atualizadoEm = Instant.now(); }
    @PreUpdate protected void preUpdate() { atualizadoEm = Instant.now(); }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getNome() { return nome; }
    public void setNome(String nome) { this.nome = nome; }
    public String getEndereco() { return endereco; }
    public void setEndereco(String endereco) { this.endereco = endereco; }
}
