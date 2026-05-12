package br.ufpb.dsc.cirurgias.repository;

import br.ufpb.dsc.cirurgias.domain.TipoCirurgia;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface TipoCirurgiaRepository extends JpaRepository<TipoCirurgia, Long> {
}
